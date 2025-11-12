"""
数据模型测试
Tests for Pydantic data models
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.schemas import (
    SystemMessage,
    UserMessage,
    AssistantMessage,
    WorkflowAgent,
    WorkflowPrompt,
    WorkflowTool,
    Workflow,
    Project,
    Conversation,
    AgentType,
    PromptType,
    OutputVisibility,
    ControlType,
)


class TestMessageModels:
    """消息模型测试"""
    
    def test_system_message(self):
        """测试：创建系统消息"""
        msg = SystemMessage(role="system", content="You are a helpful assistant")
        
        assert msg.role == "system"
        assert msg.content == "You are a helpful assistant"
        assert msg.timestamp is None
    
    def test_user_message(self):
        """测试：创建用户消息"""
        msg = UserMessage(role="user", content="Hello!")
        
        assert msg.role == "user"
        assert msg.content == "Hello!"
    
    def test_assistant_message(self):
        """测试：创建助手消息"""
        msg = AssistantMessage(
            role="assistant",
            content="Hi there!",
            agentName="MainAgent",
            responseType="external"
        )
        
        assert msg.role == "assistant"
        assert msg.content == "Hi there!"
        assert msg.agent_name == "MainAgent"
        assert msg.response_type == "external"
    
    def test_assistant_message_with_snake_case(self):
        """测试：使用snake_case创建助手消息"""
        msg = AssistantMessage(
            role="assistant",
            content="Hi there!",
            agent_name="MainAgent",
            response_type="external"
        )
        
        assert msg.agent_name == "MainAgent"
        assert msg.response_type == "external"


class TestWorkflowAgentModel:
    """WorkflowAgent模型测试"""
    
    def test_create_workflow_agent(self):
        """测试：创建工作流智能体"""
        agent = WorkflowAgent(
            name="MainAgent",
            type=AgentType.CONVERSATION,
            description="Main conversation agent",
            instructions="Be helpful and friendly",
            model="gpt-4",
            outputVisibility=OutputVisibility.USER_FACING,
            controlType=ControlType.RETAIN
        )
        
        assert agent.name == "MainAgent"
        assert agent.type == AgentType.CONVERSATION
        assert agent.output_visibility == OutputVisibility.USER_FACING
        assert agent.control_type == ControlType.RETAIN
        assert agent.disabled is False
        assert agent.locked is False
    
    def test_workflow_agent_with_rag(self):
        """测试：带RAG配置的智能体"""
        agent = WorkflowAgent(
            name="RAGAgent",
            type=AgentType.CONVERSATION,
            description="Agent with RAG",
            instructions="Use RAG to answer",
            model="gpt-4",
            ragDataSources=["source1", "source2"],
            ragK=5,
            outputVisibility=OutputVisibility.USER_FACING,
            controlType=ControlType.RETAIN
        )
        
        assert agent.rag_data_sources == ["source1", "source2"]
        assert agent.rag_k == 5
    
    def test_workflow_agent_default_values(self):
        """测试：智能体默认值"""
        agent = WorkflowAgent(
            name="TestAgent",
            type=AgentType.CONVERSATION,
            description="Test agent",
            instructions="Test instructions",
            model="gpt-4",
            outputVisibility=OutputVisibility.USER_FACING,
            controlType=ControlType.RETAIN
        )
        
        assert agent.disabled is False
        assert agent.locked is False
        assert agent.toggle_able is True
        assert agent.global_agent is False
        assert agent.rag_k == 3
        assert agent.max_calls_per_parent_agent == 3


class TestWorkflowPromptModel:
    """WorkflowPrompt模型测试"""
    
    def test_create_workflow_prompt(self):
        """测试：创建工作流提示词"""
        prompt = WorkflowPrompt(
            name="BasePrompt",
            type=PromptType.BASE_PROMPT,
            prompt="You are a helpful assistant"
        )
        
        assert prompt.name == "BasePrompt"
        assert prompt.type == PromptType.BASE_PROMPT
        assert prompt.prompt == "You are a helpful assistant"
    
    def test_workflow_prompt_types(self):
        """测试：不同类型的提示词"""
        greeting = WorkflowPrompt(
            name="Greeting",
            type=PromptType.GREETING,
            prompt="Hello! How can I help you?"
        )
        
        assert greeting.type == PromptType.GREETING


class TestWorkflowToolModel:
    """WorkflowTool模型测试"""
    
    def test_create_workflow_tool(self):
        """测试：创建工作流工具"""
        tool = WorkflowTool(
            name="search",
            description="Search the web",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        )
        
        assert tool.name == "search"
        assert tool.description == "Search the web"
        assert tool.mock_tool is False
        assert tool.is_mcp is False
    
    def test_workflow_tool_with_composio(self):
        """测试：带Composio配置的工具"""
        tool = WorkflowTool(
            name="github_create_issue",
            description="Create GitHub issue",
            parameters={"type": "object", "properties": {}},
            isComposio=True,
            composioData={
                "slug": "GITHUB_CREATE_ISSUE",
                "noAuth": False,
                "toolkitName": "GitHub",
                "toolkitSlug": "GITHUB",
                "logo": "https://example.com/logo.png"
            }
        )
        
        assert tool.is_composio is True
        assert tool.composio_data is not None
        assert tool.composio_data.slug == "GITHUB_CREATE_ISSUE"


class TestWorkflowModel:
    """Workflow模型测试"""
    
    def test_create_workflow(self):
        """测试：创建工作流"""
        workflow = Workflow(
            agents=[
                WorkflowAgent(
                    name="MainAgent",
                    type=AgentType.CONVERSATION,
                    description="Main agent",
                    instructions="Be helpful",
                    model="gpt-4",
                    outputVisibility=OutputVisibility.USER_FACING,
                    controlType=ControlType.RETAIN
                )
            ],
            prompts=[
                WorkflowPrompt(
                    name="BasePrompt",
                    type=PromptType.BASE_PROMPT,
                    prompt="You are helpful"
                )
            ],
            tools=[
                WorkflowTool(
                    name="search",
                    description="Search",
                    parameters={"type": "object", "properties": {}}
                )
            ],
            startAgentName="MainAgent"
        )
        
        assert len(workflow.agents) == 1
        assert len(workflow.prompts) == 1
        assert len(workflow.tools) == 1
        assert workflow.start_agent_name == "MainAgent"
        assert len(workflow.pipelines) == 0


class TestProjectModel:
    """Project模型测试"""
    
    def test_create_project(self):
        """测试：创建项目"""
        workflow = Workflow(
            agents=[],
            prompts=[],
            tools=[]
        )
        
        project = Project(
            id="123e4567-e89b-12d3-a456-426614174000",
            name="测试项目",
            createdAt=datetime.now(),
            createdByUserId="user123",
            secret="secret123",
            draftWorkflow=workflow,
            liveWorkflow=workflow
        )
        
        assert project.id == "123e4567-e89b-12d3-a456-426614174000"
        assert project.name == "测试项目"
        assert project.created_by_user_id == "user123"
        assert project.secret == "secret123"
    
    def test_project_with_optional_fields(self):
        """测试：带可选字段的项目"""
        workflow = Workflow(
            agents=[],
            prompts=[],
            tools=[]
        )
        
        project = Project(
            id="123e4567-e89b-12d3-a456-426614174000",
            name="测试项目",
            createdAt=datetime.now(),
            lastUpdatedAt=datetime.now(),
            createdByUserId="user123",
            secret="secret123",
            draftWorkflow=workflow,
            liveWorkflow=workflow,
            webhookUrl="https://example.com/webhook"
        )
        
        assert project.webhook_url == "https://example.com/webhook"
        assert project.last_updated_at is not None


class TestConversationModel:
    """Conversation模型测试"""
    
    def test_create_conversation(self):
        """测试：创建对话"""
        workflow = Workflow(
            agents=[],
            prompts=[],
            tools=[]
        )
        
        from app.models.schemas import Reason, ReasonType
        
        conversation = Conversation(
            id="conv123",
            projectId="proj123",
            workflow=workflow,
            reason=Reason(type=ReasonType.USER_MESSAGE),
            isLiveWorkflow=True,
            createdAt=datetime.now()
        )
        
        assert conversation.id == "conv123"
        assert conversation.project_id == "proj123"
        assert conversation.is_live_workflow is True
        assert conversation.turns is None


class TestModelValidation:
    """模型验证测试"""
    
    def test_required_fields_validation(self):
        """测试：必需字段验证"""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowAgent(
                name="TestAgent",
                type=AgentType.CONVERSATION,
                # 缺少必需字段 description, instructions, model
            )
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
    
    def test_enum_validation(self):
        """测试：枚举值验证"""
        with pytest.raises(ValidationError):
            WorkflowAgent(
                name="TestAgent",
                type="invalid_type",  # 无效的枚举值
                description="Test",
                instructions="Test",
                model="gpt-4",
                outputVisibility=OutputVisibility.USER_FACING,
                controlType=ControlType.RETAIN
            )

