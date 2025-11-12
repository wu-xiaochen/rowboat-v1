"""
Pydantic数据模型定义
Pydantic data models matching TypeScript Zod schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum


# ==================== Message Models ====================

class MessageBase(BaseModel):
    """基础消息模型"""
    timestamp: Optional[datetime] = None


class SystemMessage(MessageBase):
    """系统消息"""
    role: Literal["system"] = "system"
    content: str


class UserMessage(MessageBase):
    """用户消息"""
    role: Literal["user"] = "user"
    content: str


class AssistantMessage(MessageBase):
    """助手消息"""
    role: Literal["assistant"] = "assistant"
    content: str
    agent_name: Optional[str] = Field(None, alias="agentName")
    response_type: Literal["internal", "external"] = Field(alias="responseType")
    
    class Config:
        populate_by_name = True


class ToolCall(BaseModel):
    """工具调用"""
    id: str
    type: Literal["function"] = "function"
    function: Dict[str, str]  # {name: str, arguments: str}


class AssistantMessageWithToolCalls(MessageBase):
    """带工具调用的助手消息"""
    role: Literal["assistant"] = "assistant"
    content: None = None
    tool_calls: List[ToolCall] = Field(alias="toolCalls")
    agent_name: Optional[str] = Field(None, alias="agentName")
    
    class Config:
        populate_by_name = True


class ToolMessage(MessageBase):
    """工具消息"""
    role: Literal["tool"] = "tool"
    content: str
    tool_call_id: str = Field(alias="toolCallId")
    tool_name: str = Field(alias="toolName")
    
    class Config:
        populate_by_name = True


# Union type for all message types
Message = Union[
    SystemMessage,
    UserMessage,
    AssistantMessage,
    AssistantMessageWithToolCalls,
    ToolMessage,
]


# ==================== Workflow Models ====================

class AgentType(str, Enum):
    """智能体类型"""
    CONVERSATION = "conversation"
    POST_PROCESS = "post_process"
    ESCALATION = "escalation"
    PIPELINE = "pipeline"


class OutputVisibility(str, Enum):
    """输出可见性"""
    USER_FACING = "user_facing"
    INTERNAL = "internal"


class ControlType(str, Enum):
    """控制类型"""
    RETAIN = "retain"
    RELINQUISH_TO_PARENT = "relinquish_to_parent"
    RELINQUISH_TO_START = "relinquish_to_start"


class RAGReturnType(str, Enum):
    """RAG返回类型"""
    CHUNKS = "chunks"
    CONTENT = "content"


class WorkflowAgent(BaseModel):
    """工作流智能体"""
    name: str
    order: Optional[int] = None
    type: AgentType
    description: str
    disabled: bool = False
    instructions: str
    examples: Optional[str] = None
    model: str
    locked: bool = Field(
        default=False,
        description="Whether this agent is locked and cannot be deleted"
    )
    toggle_able: bool = Field(
        default=True,
        alias="toggleAble",
        description="Whether this agent can be enabled or disabled"
    )
    global_agent: bool = Field(
        default=False,
        alias="global",
        description="Whether this agent is a global agent"
    )
    rag_data_sources: Optional[List[str]] = Field(None, alias="ragDataSources")
    rag_return_type: RAGReturnType = Field(
        default=RAGReturnType.CHUNKS,
        alias="ragReturnType"
    )
    rag_k: int = Field(default=3, alias="ragK")
    output_visibility: OutputVisibility = Field(
        default=OutputVisibility.USER_FACING,
        alias="outputVisibility"
    )
    control_type: Optional[ControlType] = Field(None, alias="controlType")
    max_calls_per_parent_agent: int = Field(
        default=3,
        alias="maxCallsPerParentAgent",
        description="Maximum number of times this agent can be called by a parent agent"
    )
    
    class Config:
        populate_by_name = True
        use_enum_values = True


class PromptType(str, Enum):
    """提示词类型"""
    BASE_PROMPT = "base_prompt"
    STYLE_PROMPT = "style_prompt"
    GREETING = "greeting"


class WorkflowPrompt(BaseModel):
    """工作流提示词"""
    name: str
    type: PromptType
    prompt: str
    
    class Config:
        use_enum_values = True


class ComposioToolData(BaseModel):
    """Composio工具数据"""
    slug: str
    no_auth: bool = Field(alias="noAuth")
    toolkit_name: str = Field(alias="toolkitName")
    toolkit_slug: str = Field(alias="toolkitSlug")
    logo: str
    
    class Config:
        populate_by_name = True


class WorkflowTool(BaseModel):
    """工作流工具"""
    name: str
    description: str
    mock_tool: bool = Field(default=False, alias="mockTool")
    mock_instructions: Optional[str] = Field(None, alias="mockInstructions")
    parameters: Dict[str, Any]
    is_mcp: bool = Field(default=False, alias="isMcp")
    mcp_server_name: Optional[str] = Field(None, alias="mcpServerName")
    is_composio: Optional[bool] = Field(None, alias="isComposio")
    is_library: bool = Field(default=False, alias="isLibrary")
    is_webhook: Optional[bool] = Field(None, alias="isWebhook")
    is_gemini_image: Optional[bool] = Field(None, alias="isGeminiImage")
    composio_data: Optional[ComposioToolData] = Field(None, alias="composioData")
    
    class Config:
        populate_by_name = True


class WorkflowPipeline(BaseModel):
    """工作流管道"""
    name: str
    description: Optional[str] = None
    agents: List[str]  # ordered list of agent names
    order: Optional[int] = None


class Workflow(BaseModel):
    """工作流"""
    agents: List[WorkflowAgent]
    prompts: List[WorkflowPrompt]
    tools: List[WorkflowTool]
    pipelines: List[WorkflowPipeline] = []
    start_agent_name: Optional[str] = Field(None, alias="startAgentName")
    
    class Config:
        populate_by_name = True


# ==================== Core Entity Models ====================

class ComposioConnectedAccount(BaseModel):
    """Composio连接账户"""
    id: str
    auth_config_id: str = Field(alias="authConfigId")
    status: Literal["INITIATED", "ACTIVE", "FAILED"]
    created_at: datetime = Field(alias="createdAt")
    last_updated_at: datetime = Field(alias="lastUpdatedAt")
    
    class Config:
        populate_by_name = True


class CustomMcpServer(BaseModel):
    """自定义MCP服务器"""
    server_url: str = Field(alias="serverUrl")
    
    class Config:
        populate_by_name = True


class Project(BaseModel):
    """项目模型"""
    id: str
    name: str
    created_at: datetime = Field(alias="createdAt")
    last_updated_at: Optional[datetime] = Field(None, alias="lastUpdatedAt")
    created_by_user_id: str = Field(alias="createdByUserId")
    secret: str
    draft_workflow: Workflow = Field(alias="draftWorkflow")
    live_workflow: Workflow = Field(alias="liveWorkflow")
    webhook_url: Optional[str] = Field(None, alias="webhookUrl")
    composio_connected_accounts: Optional[Dict[str, ComposioConnectedAccount]] = Field(
        None,
        alias="composioConnectedAccounts"
    )
    custom_mcp_servers: Optional[Dict[str, CustomMcpServer]] = Field(
        None,
        alias="customMcpServers"
    )
    
    class Config:
        populate_by_name = True


class ReasonType(str, Enum):
    """原因类型"""
    USER_MESSAGE = "user_message"
    COMPOSIO_TRIGGER = "composio_trigger"
    SCHEDULED_JOB_RULE = "scheduled_job_rule"
    RECURRING_JOB_RULE = "recurring_job_rule"


class Reason(BaseModel):
    """对话原因"""
    type: ReasonType
    # 根据type不同，可能有额外字段
    trigger_id: Optional[str] = Field(None, alias="triggerId")
    trigger_deployment_id: Optional[str] = Field(None, alias="triggerDeploymentId")
    trigger_type_slug: Optional[str] = Field(None, alias="triggerTypeSlug")
    payload: Optional[Dict[str, Any]] = None
    rule_id: Optional[str] = Field(None, alias="ruleId")
    
    class Config:
        populate_by_name = True
        use_enum_values = True


class Turn(BaseModel):
    """对话轮次"""
    id: str
    conversation_id: str = Field(alias="conversationId")
    messages: List[Message]
    created_at: datetime = Field(alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")
    
    class Config:
        populate_by_name = True


class Conversation(BaseModel):
    """对话模型"""
    id: str
    project_id: str = Field(alias="projectId")
    workflow: Workflow
    reason: Reason
    is_live_workflow: bool = Field(alias="isLiveWorkflow")
    turns: Optional[List[Turn]] = None
    created_at: datetime = Field(alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")
    
    class Config:
        populate_by_name = True


class DataSourceStatus(str, Enum):
    """数据源状态"""
    PENDING = "pending"
    READY = "ready"
    ERROR = "error"
    DELETED = "deleted"


class DataSourceType(str, Enum):
    """数据源类型"""
    URLS = "urls"
    FILES_LOCAL = "files_local"
    FILES_S3 = "files_s3"
    TEXT = "text"


class DataSourceData(BaseModel):
    """数据源数据"""
    type: DataSourceType
    
    class Config:
        use_enum_values = True


class DataSource(BaseModel):
    """数据源模型"""
    id: str
    name: str
    description: str
    project_id: str = Field(alias="projectId")
    active: bool = True
    status: DataSourceStatus
    version: int
    error: Optional[str] = None
    billing_error: Optional[str] = Field(None, alias="billingError")
    created_at: datetime = Field(alias="createdAt")
    last_updated_at: Optional[datetime] = Field(None, alias="lastUpdatedAt")
    attempts: int
    last_attempt_at: Optional[datetime] = Field(None, alias="lastAttemptAt")
    data: DataSourceData
    
    class Config:
        populate_by_name = True
        use_enum_values = True


class JobStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobInput(BaseModel):
    """任务输入"""
    messages: List[Message]


class JobOutput(BaseModel):
    """任务输出"""
    conversation_id: Optional[str] = Field(None, alias="conversationId")
    turn_id: Optional[str] = Field(None, alias="turnId")
    error: Optional[str] = None
    
    class Config:
        populate_by_name = True


class Job(BaseModel):
    """任务模型"""
    id: str
    reason: Reason
    project_id: str = Field(alias="projectId")
    input: JobInput
    output: Optional[JobOutput] = None
    worker_id: Optional[str] = Field(None, alias="workerId")
    last_worker_id: Optional[str] = Field(None, alias="lastWorkerId")
    status: JobStatus
    created_at: datetime = Field(alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")
    
    class Config:
        populate_by_name = True
        use_enum_values = True

