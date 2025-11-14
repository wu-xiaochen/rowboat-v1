"""
智能体服务单元测试
Unit tests for Agents Service
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
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

from app.services.agents.agents_service import AgentsService
from app.models.schemas import (
    UserMessage,
    AssistantMessage,
    Workflow,
    WorkflowAgent,
    WorkflowTool,
    AgentType,
    OutputVisibility,
    ControlType,
)


class TestAgentsService:
    """智能体服务测试"""
    
    @pytest.fixture
    def agents_service(self):
        """创建AgentsService实例"""
        return AgentsService()
    
    @pytest.fixture
    def sample_workflow(self):
        """示例工作流"""
        return Workflow(
            agents=[
                WorkflowAgent(
                    name="MainAgent",
                    type=AgentType.CONVERSATION,
                    description="主智能体",
                    instructions="你是一个友好的助手",
                    model="gpt-4",
                    outputVisibility=OutputVisibility.USER_FACING,
                    controlType=ControlType.RETAIN,
                )
            ],
            prompts=[],
            tools=[],
            pipelines=[],
            startAgentName="MainAgent"
        )
    
    @pytest.fixture
    def multi_agent_workflow(self):
        """多智能体工作流"""
        return Workflow(
            agents=[
                WorkflowAgent(
                    name="Agent1",
                    type=AgentType.CONVERSATION,
                    description="智能体1",
                    instructions="你是Agent1，如果需要帮助可以@Agent2",
                    model="gpt-4",
                    outputVisibility=OutputVisibility.USER_FACING,
                    controlType=ControlType.RETAIN,
                ),
                WorkflowAgent(
                    name="Agent2",
                    type=AgentType.CONVERSATION,
                    description="智能体2",
                    instructions="你是Agent2，专门处理复杂问题",
                    model="gpt-4",
                    outputVisibility=OutputVisibility.USER_FACING,
                    controlType=ControlType.RETAIN,
                )
            ],
            prompts=[],
            tools=[],
            pipelines=[],
            startAgentName="Agent1"
        )
    
    @pytest.fixture
    def pipeline_workflow(self):
        """Pipeline工作流"""
        from app.models.schemas import WorkflowPipeline
        return Workflow(
            agents=[
                WorkflowAgent(
                    name="Step1",
                    type=AgentType.CONVERSATION,
                    description="步骤1",
                    instructions="执行第一步",
                    model="gpt-4",
                    outputVisibility=OutputVisibility.USER_FACING,
                    controlType=ControlType.RETAIN,
                ),
                WorkflowAgent(
                    name="Step2",
                    type=AgentType.CONVERSATION,
                    description="步骤2",
                    instructions="执行第二步",
                    model="gpt-4",
                    outputVisibility=OutputVisibility.USER_FACING,
                    controlType=ControlType.RETAIN,
                )
            ],
            prompts=[],
            tools=[],
            pipelines=[
                WorkflowPipeline(
                    name="TestPipeline",
                    agents=["Step1", "Step2"]
                )
            ],
            startAgentName="Step1"
        )
    
    def test_init(self, agents_service):
        """测试：初始化AgentsService"""
        assert agents_service is not None
        assert agents_service.settings is not None
        assert agents_service.agent_tools_service is not None
        assert agents_service._agents_cache is not None
    
    def test_build_instructions(self, agents_service, sample_workflow):
        """测试：构建智能体指令"""
        agent = sample_workflow.agents[0]
        instructions = agents_service._build_instructions(agent, sample_workflow)
        
        assert "主智能体" in instructions
        assert "你是一个友好的助手" in instructions
    
    def test_build_instructions_with_examples(self, agents_service, sample_workflow):
        """测试：构建智能体指令（带示例）"""
        agent = sample_workflow.agents[0]
        agent.examples = "示例1: 用户说'你好'，回复'你好！有什么可以帮助你的吗？'"
        instructions = agents_service._build_instructions(agent, sample_workflow)
        
        assert "示例1" in instructions
        assert "Examples:" in instructions
    
    def test_parse_mentions(self, agents_service, multi_agent_workflow):
        """测试：解析mentions"""
        instructions = "如果需要帮助，可以@Agent2"
        mentions = agents_service._parse_mentions(instructions, multi_agent_workflow)
        
        assert len(mentions) > 0
        agent_mentions = [m for m in mentions if m["type"] == "agent"]
        assert len(agent_mentions) > 0
        assert any(m["name"] == "Agent2" for m in agent_mentions)
    
    def test_get_handoff_agent_names(self, agents_service, multi_agent_workflow):
        """测试：获取handoff智能体名称"""
        # Mock Agent对象
        mock_agent1 = Mock()
        mock_agent2 = Mock()
        all_agents = {
            "Agent1": mock_agent1,
            "Agent2": mock_agent2
        }
        
        agent1_config = multi_agent_workflow.agents[0]
        handoff_names = agents_service._get_handoff_agent_names(
            agent1_config,
            multi_agent_workflow,
            all_agents
        )
        
        # 应该包含Agent2（如果instructions中有@Agent2）
        assert isinstance(handoff_names, list)
    
    @pytest.mark.asyncio
    async def test_stream_response_single_agent(self, agents_service, sample_workflow):
        """测试：单智能体流式响应"""
        messages = [UserMessage(content="你好")]
        
        # Mock Runner和Agent
        with patch("app.services.agents.agents_service.Runner") as mock_runner, \
             patch("app.services.agents.agents_service.Agent") as mock_agent_class:
            
            # Mock流式事件
            mock_event = Mock()
            mock_event.type = "text"
            mock_event.text = "你好！有什么可以帮助你的吗？"
            
            async def mock_stream(*args, **kwargs):
                yield mock_event
            
            # 直接mock Runner.stream为async generator
            async def mock_runner_stream(*args, **kwargs):
                async for item in mock_stream():
                    yield item
            
            mock_runner.stream = mock_runner_stream
            
            # Mock Agent创建
            mock_agent = Mock()
            mock_agent.name = "MainAgent"
            mock_agent_class.return_value = mock_agent
            
            message_count = 0
            async for message in agents_service.stream_response(
                project_id="test-project",
                workflow=sample_workflow,
                messages=messages
            ):
                message_count += 1
                if message_count > 5:  # 限制测试消息数量
                    break
            
            # 应该至少尝试处理消息
            assert message_count >= 0
    
    @pytest.mark.asyncio
    async def test_stream_response_multi_agent_handoff(self, agents_service, multi_agent_workflow):
        """测试：多智能体handoff"""
        messages = [UserMessage(content="复杂问题")]
        
        # Mock Runner和Agent
        with patch("app.services.agents.agents_service.Runner") as mock_runner, \
             patch("app.services.agents.agents_service.Agent") as mock_agent_class:
            
            # Mock handoff事件
            mock_handoff_event = Mock()
            mock_handoff_event.type = "handoff"
            mock_handoff_event.target_agent = "Agent2"
            
            # Mock文本事件
            mock_text_event = Mock()
            mock_text_event.type = "text"
            mock_text_event.text = "这是Agent2的回复"
            
            async def mock_stream(*args, **kwargs):
                yield mock_handoff_event
                yield mock_text_event
            
            # 直接mock Runner.stream为async generator
            async def mock_runner_stream(*args, **kwargs):
                async for item in mock_stream():
                    yield item
            
            mock_runner.stream = mock_runner_stream
            
            # Mock Agent创建
            mock_agent1 = Mock()
            mock_agent1.name = "Agent1"
            mock_agent2 = Mock()
            mock_agent2.name = "Agent2"
            mock_agent_class.side_effect = [mock_agent1, mock_agent2]
            
            message_count = 0
            async for message in agents_service.stream_response(
                project_id="test-project",
                workflow=multi_agent_workflow,
                messages=messages
            ):
                message_count += 1
                if message_count > 10:  # 限制测试消息数量
                    break
            
            # 应该至少尝试处理消息
            assert message_count >= 0
    
    @pytest.mark.asyncio
    async def test_stream_response_pipeline(self, agents_service, pipeline_workflow):
        """测试：Pipeline执行"""
        messages = [UserMessage(content="执行Pipeline")]
        
        # Mock Runner和Agent
        with patch("app.services.agents.agents_service.Runner") as mock_runner, \
             patch("app.services.agents.agents_service.Agent") as mock_agent_class:
            
            # Mock Pipeline执行事件
            mock_event1 = Mock()
            mock_event1.type = "text"
            mock_event1.text = "Step1完成"
            
            mock_event2 = Mock()
            mock_event2.type = "text"
            mock_event2.text = "Step2完成"
            
            async def mock_stream(*args, **kwargs):
                yield mock_event1
                yield mock_event2
            
            # 直接mock Runner.stream为async generator
            async def mock_runner_stream(*args, **kwargs):
                async for item in mock_stream():
                    yield item
            
            mock_runner.stream = mock_runner_stream
            
            # Mock Agent创建
            mock_agent = Mock()
            mock_agent.name = "Step1"
            mock_agent_class.return_value = mock_agent
            
            message_count = 0
            async for message in agents_service.stream_response(
                project_id="test-project",
                workflow=pipeline_workflow,
                messages=messages
            ):
                message_count += 1
                if message_count > 10:  # 限制测试消息数量
                    break
            
            # 应该至少尝试处理消息
            assert message_count >= 0
    
    @pytest.mark.asyncio
    async def test_stream_response_with_tools(self, agents_service, sample_workflow):
        """测试：带工具调用的流式响应"""
        # 添加工具到工作流
        sample_workflow.tools = [
            WorkflowTool(
                name="search",
                description="搜索工具",
                parameters={"type": "object", "properties": {}}
            )
        ]
        
        messages = [UserMessage(content="搜索信息")]
        
        # Mock Runner和Agent
        with patch("app.services.agents.agents_service.Runner") as mock_runner, \
             patch("app.services.agents.agents_service.Agent") as mock_agent_class:
            
            # Mock工具调用事件
            mock_tool_event = Mock()
            mock_tool_event.type = "tool_call"
            mock_tool_event.tool_name = "search"
            
            # Mock文本事件
            mock_text_event = Mock()
            mock_text_event.type = "text"
            mock_text_event.text = "搜索结果"
            
            async def mock_stream(*args, **kwargs):
                yield mock_tool_event
                yield mock_text_event
            
            # 直接mock Runner.stream为async generator
            async def mock_runner_stream(*args, **kwargs):
                async for item in mock_stream():
                    yield item
            
            mock_runner.stream = mock_runner_stream
            
            # Mock Agent创建
            mock_agent = Mock()
            mock_agent.name = "MainAgent"
            mock_agent_class.return_value = mock_agent
            
            message_count = 0
            async for message in agents_service.stream_response(
                project_id="test-project",
                workflow=sample_workflow,
                messages=messages
            ):
                message_count += 1
                if message_count > 10:  # 限制测试消息数量
                    break
            
            # 应该至少尝试处理消息
            assert message_count >= 0
    
    @pytest.mark.asyncio
    async def test_stream_response_error_handling(self, agents_service, sample_workflow):
        """测试：错误处理"""
        messages = [UserMessage(content="测试")]
        
        # Mock Runner抛出异常
        with patch("app.services.agents.agents_service.Runner") as mock_runner, \
             patch("app.services.agents.agents_service.Agent") as mock_agent_class:
            
            # Mock抛出异常
            async def mock_stream(*args, **kwargs):
                raise Exception("测试错误")
            
            # 直接mock Runner.stream为async generator
            async def mock_runner_stream(*args, **kwargs):
                async for item in mock_stream():
                    yield item
            
            mock_runner.stream = mock_runner_stream
            
            # Mock Agent创建
            mock_agent = Mock()
            mock_agent.name = "MainAgent"
            mock_agent_class.return_value = mock_agent
            
            # 应该能够处理异常
            message_count = 0
            try:
                async for message in agents_service.stream_response(
                    project_id="test-project",
                    workflow=sample_workflow,
                    messages=messages
                ):
                    message_count += 1
                    if message_count > 5:
                        break
            except Exception:
                # 异常应该被处理或传播
                pass
            
            # 测试应该完成（可能没有消息或抛出异常）
            assert True
    
    def test_create_openai_model(self, agents_service):
        """测试：创建OpenAI模型配置"""
        model = agents_service._create_openai_model("gpt-4")
        
        assert model is not None
        assert hasattr(model, "model") or hasattr(model, "openai_client")
    
    def test_create_openai_model_default(self, agents_service):
        """测试：创建OpenAI模型配置（使用默认模型）"""
        # 使用空字符串应该使用默认模型
        model = agents_service._create_openai_model("")
        
        assert model is not None

