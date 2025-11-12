"""
Copilot服务单元测试
Unit tests for Copilot Service
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List

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

from app.services.copilot.copilot_service import CopilotService
from app.models.copilot_schemas import (
    CopilotUserMessage,
    CopilotAssistantMessage,
    CopilotChatContextAgent,
    DataSourceForCopilot,
    EditAgentInstructionsResponse,
)


class TestCopilotService:
    """Copilot服务测试"""
    
    @pytest.fixture
    def copilot_service(self):
        """创建CopilotService实例"""
        return CopilotService()
    
    @pytest.fixture
    def sample_messages(self):
        """示例消息"""
        return [
            CopilotUserMessage(content="Hello"),
            CopilotAssistantMessage(content="Hi there!"),
        ]
    
    @pytest.fixture
    def sample_workflow(self):
        """示例工作流"""
        return {
            "agents": [],
            "prompts": [],
            "tools": [],
            "pipelines": [],
            "startAgentName": None,
        }
    
    def test_init(self, copilot_service):
        """测试：初始化CopilotService"""
        assert copilot_service is not None
        assert copilot_service.settings is not None
        assert copilot_service.prompt_loader is not None
        assert copilot_service.llm is not None
        assert copilot_service.edit_agent_llm is not None
    
    def test_get_context_prompt_agent(self, copilot_service):
        """测试：获取智能体上下文提示词"""
        context = CopilotChatContextAgent(name="Test Agent")
        prompt = copilot_service._get_context_prompt(context)
        
        assert "Test Agent" in prompt
        assert "agent" in prompt.lower()
    
    def test_get_context_prompt_none(self, copilot_service):
        """测试：获取空上下文提示词"""
        prompt = copilot_service._get_context_prompt(None)
        assert prompt == ""
    
    def test_get_current_workflow_prompt(self, copilot_service, sample_workflow):
        """测试：获取当前工作流提示词"""
        prompt = copilot_service._get_current_workflow_prompt(sample_workflow)
        
        assert "workflow" in prompt.lower()
        assert "agents" in prompt
    
    def test_get_data_sources_prompt(self, copilot_service):
        """测试：获取数据源提示词"""
        data_sources = [
            DataSourceForCopilot(
                id="ds1",
                name="Test Source",
                description="Test description",
                data={"type": "text"},
            )
        ]
        prompt = copilot_service._get_data_sources_prompt(data_sources)
        
        assert "data sources" in prompt.lower()
        assert "Test Source" in prompt
    
    def test_get_data_sources_prompt_empty(self, copilot_service):
        """测试：获取空数据源提示词"""
        prompt = copilot_service._get_data_sources_prompt(None)
        assert prompt == ""
    
    def test_convert_messages(self, copilot_service, sample_messages):
        """测试：转换消息格式"""
        langchain_messages = copilot_service._convert_messages(sample_messages)
        
        assert len(langchain_messages) == 2
        assert langchain_messages[0].__class__.__name__ == "HumanMessage"
        assert langchain_messages[1].__class__.__name__ == "AIMessage"
    
    def test_build_system_prompt(self, copilot_service, sample_workflow):
        """测试：构建系统提示词"""
        system_prompt = copilot_service._build_system_prompt(sample_workflow)
        
        assert system_prompt is not None
        assert len(system_prompt) > 0
        # 验证占位符被替换
        assert "{agent_model}" not in system_prompt
        assert "{workflow_schema}" not in system_prompt
    
    @pytest.mark.asyncio
    async def test_stream_response_basic(self, copilot_service, sample_messages, sample_workflow):
        """测试：基础流式响应"""
        # Mock LLM响应
        mock_chunk = MagicMock()
        mock_chunk.content = "Hello"
        mock_chunk.response_metadata = {}
        
        # 创建异步生成器
        async def mock_astream(*args, **kwargs):
            yield mock_chunk
        
        # 创建Mock LLM对象
        mock_llm = MagicMock()
        # 直接返回异步生成器，而不是使用AsyncMock
        mock_llm.astream = mock_astream
        # 如果没有工具，直接使用llm.astream；如果有工具，使用bind_tools后的astream
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)
        
        # 清空工具列表，避免使用bind_tools
        copilot_service.tools = []
        # 替换llm对象
        copilot_service.llm = mock_llm
        
        events = []
        async for event in copilot_service.stream_response(
            project_id="test-project",
            messages=sample_messages,
            workflow=sample_workflow,
        ):
            events.append(event)
        
        assert len(events) > 0
        assert events[0].content == "Hello"
    
    @pytest.mark.asyncio
    async def test_get_edit_agent_instructions(self, copilot_service, sample_messages, sample_workflow):
        """测试：获取编辑智能体提示词"""
        # Mock LLM响应
        mock_response = MagicMock()
        mock_response.content = '{"agent_instructions": "Test instructions"}'
        
        # 创建Mock LLM对象
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        
        # 替换edit_agent_llm对象
        copilot_service.edit_agent_llm = mock_llm
        
        result = await copilot_service.get_edit_agent_instructions(
            project_id="test-project",
            messages=sample_messages,
            workflow=sample_workflow,
        )
        
        assert isinstance(result, EditAgentInstructionsResponse)
        assert result.agent_instructions == "Test instructions"

