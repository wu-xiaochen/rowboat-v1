"""
Copilot端点集成测试
Integration tests for Copilot endpoints
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
from app.models.copilot_schemas import (
    CopilotStreamEvent,
    EditAgentInstructionsResponse,
)


class TestCopilotEndpoints:
    """Copilot端点测试"""
    
    @pytest.mark.asyncio
    async def test_copilot_stream_success(self):
        """测试：Copilot流式响应成功"""
        # Mock Copilot服务
        with patch("app.api.v1.endpoints.copilot.get_copilot_service") as mock_service:
            mock_service_instance = AsyncMock()
            
            # Mock流式响应
            async def mock_stream_response(*args, **kwargs):
                # 模拟消息事件
                yield CopilotStreamEvent(
                    type=None,
                    content="你好！我可以帮你创建智能体。"
                )
                # 模拟完成事件
                yield CopilotStreamEvent(type="done")
            
            mock_service_instance.stream_response = mock_stream_response
            mock_service.return_value = mock_service_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as client:
                response = await client.post(
                    "/api/v1/proj123/copilot/stream",
                    json={
                        "projectId": "proj123",
                        "messages": [
                            {
                                "role": "user",
                                "content": "帮我创建一个智能客服"
                            }
                        ],
                        "workflow": {
                            "agents": [],
                            "tools": [],
                            "prompts": [],
                            "pipelines": [],
                            "startAgentName": None
                        }
                    }
                )
                
                assert response.status_code == 200
                assert response.headers.get("content-type") == "text/event-stream; charset=utf-8"
                
                # 读取流式响应
                content = await response.aread()
                content_str = content.decode('utf-8')
                
                # 验证SSE格式
                assert "event: message" in content_str or "event: done" in content_str
                assert "data:" in content_str
    
    @pytest.mark.asyncio
    async def test_copilot_stream_with_tool_call(self):
        """测试：Copilot流式响应（带工具调用）"""
        # Mock Copilot服务
        with patch("app.api.v1.endpoints.copilot.get_copilot_service") as mock_service:
            mock_service_instance = AsyncMock()
            
            # Mock流式响应（包含工具调用）
            async def mock_stream_response(*args, **kwargs):
                # 模拟工具调用事件
                yield CopilotStreamEvent(
                    type="tool-call",
                    tool_name="create_agent",
                    args={"name": "智能客服", "instructions": "你是一个智能客服"}
                )
                # 模拟完成事件
                yield CopilotStreamEvent(type="done")
            
            mock_service_instance.stream_response = mock_stream_response
            mock_service.return_value = mock_service_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as client:
                response = await client.post(
                    "/api/v1/proj123/copilot/stream",
                    json={
                        "projectId": "proj123",
                        "messages": [
                            {
                                "role": "user",
                                "content": "创建一个智能客服"
                            }
                        ],
                        "workflow": {
                            "agents": [],
                            "tools": [],
                            "prompts": [],
                            "pipelines": [],
                            "startAgentName": None
                        }
                    }
                )
                
                assert response.status_code == 200
                assert response.headers.get("content-type") == "text/event-stream; charset=utf-8"
                
                # 读取流式响应
                content = await response.aread()
                content_str = content.decode('utf-8')
                
                # 验证包含工具调用事件
                assert "tool-call" in content_str or "toolName" in content_str
    
    @pytest.mark.asyncio
    async def test_copilot_stream_project_id_mismatch(self):
        """测试：Copilot流式响应失败（项目ID不匹配）"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/proj123/copilot/stream",
                json={
                    "projectId": "different_proj",  # 项目ID不匹配
                    "messages": [
                        {
                            "role": "user",
                            "content": "测试"
                        }
                    ],
                    "workflow": {
                        "agents": [],
                        "tools": [],
                        "prompts": [],
                        "pipelines": [],
                        "startAgentName": None
                    }
                }
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "项目ID不匹配" in data.get("detail", "")
    
    @pytest.mark.asyncio
    async def test_copilot_stream_invalid_request(self):
        """测试：Copilot流式响应失败（无效请求）"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 缺少必需字段
            response = await client.post(
                "/api/v1/proj123/copilot/stream",
                json={}
            )
            
            assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_copilot_stream_error_handling(self):
        """测试：Copilot流式响应错误处理"""
        # Mock Copilot服务抛出异常
        with patch("app.api.v1.endpoints.copilot.get_copilot_service") as mock_service:
            mock_service_instance = AsyncMock()
            
            # Mock抛出异常
            async def mock_stream_response(*args, **kwargs):
                raise Exception("测试错误")
            
            mock_service_instance.stream_response = mock_stream_response
            mock_service.return_value = mock_service_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as client:
                response = await client.post(
                    "/api/v1/proj123/copilot/stream",
                    json={
                        "projectId": "proj123",
                        "messages": [
                            {
                                "role": "user",
                                "content": "测试"
                            }
                        ],
                        "workflow": {
                            "agents": [],
                            "tools": [],
                            "prompts": [],
                            "pipelines": [],
                            "startAgentName": None
                        }
                    }
                )
                
                assert response.status_code == 200  # 流式响应仍然返回200
                
                # 读取流式响应，应该包含错误事件
                content = await response.aread()
                content_str = content.decode('utf-8')
                
                # 验证包含错误事件
                assert "event: error" in content_str or "测试错误" in content_str
    
    @pytest.mark.asyncio
    async def test_edit_agent_instructions_success(self):
        """测试：编辑智能体提示词成功"""
        # Mock Copilot服务
        with patch("app.api.v1.endpoints.copilot.get_copilot_service") as mock_service:
            mock_service_instance = AsyncMock()
            
            # Mock编辑智能体提示词响应
            mock_response = EditAgentInstructionsResponse(
                agent_instructions="你是一个专业的智能客服，能够友好地回答用户的问题。"
            )
            
            mock_service_instance.get_edit_agent_instructions = AsyncMock(return_value=mock_response)
            mock_service.return_value = mock_service_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/proj123/copilot/edit-agent-instructions",
                    json={
                        "projectId": "proj123",
                        "messages": [
                            {
                                "role": "user",
                                "content": "修改智能体的提示词，让它更专业"
                            }
                        ],
                        "workflow": {
                            "agents": [],
                            "tools": [],
                            "prompts": [],
                            "pipelines": [],
                            "startAgentName": None
                        },
                        "context": {
                            "type": "agent",
                            "name": "智能客服"
                        }
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "agentInstructions" in data or "agent_instructions" in data
                instructions = data.get("agentInstructions") or data.get("agent_instructions")
                assert len(instructions) > 0
    
    @pytest.mark.asyncio
    async def test_edit_agent_instructions_project_id_mismatch(self):
        """测试：编辑智能体提示词失败（项目ID不匹配）"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/proj123/copilot/edit-agent-instructions",
                json={
                    "projectId": "different_proj",  # 项目ID不匹配
                    "messages": [
                        {
                            "role": "user",
                            "content": "测试"
                        }
                    ],
                    "workflow": {
                        "agents": [],
                        "tools": [],
                        "prompts": [],
                        "pipelines": [],
                        "startAgentName": None
                    },
                    "context": {
                        "type": "agent",
                        "name": "测试智能体"
                    }
                }
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "项目ID不匹配" in data.get("detail", "")
    
    @pytest.mark.asyncio
    async def test_edit_agent_instructions_invalid_request(self):
        """测试：编辑智能体提示词失败（无效请求）"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 缺少必需字段
            response = await client.post(
                "/api/v1/proj123/copilot/edit-agent-instructions",
                json={}
            )
            
            assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_edit_agent_instructions_error_handling(self):
        """测试：编辑智能体提示词错误处理"""
        # Mock Copilot服务抛出异常
        with patch("app.api.v1.endpoints.copilot.get_copilot_service") as mock_service:
            mock_service_instance = AsyncMock()
            
            # Mock抛出异常
            mock_service_instance.get_edit_agent_instructions = AsyncMock(
                side_effect=Exception("服务错误")
            )
            mock_service.return_value = mock_service_instance
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/proj123/copilot/edit-agent-instructions",
                    json={
                        "projectId": "proj123",
                        "messages": [
                            {
                                "role": "user",
                                "content": "测试"
                            }
                        ],
                        "workflow": {
                            "agents": [],
                            "tools": [],
                            "prompts": [],
                            "pipelines": [],
                            "startAgentName": None
                        },
                        "context": {
                            "type": "agent",
                            "name": "测试智能体"
                        }
                    }
                )
                
                assert response.status_code == 500
                data = response.json()
                assert "服务错误" in data.get("detail", "")

