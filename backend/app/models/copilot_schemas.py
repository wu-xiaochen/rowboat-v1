"""
Copilot相关数据模型
Copilot-related data models
"""

from typing import Any, Dict, List, Literal, Optional, Union, Annotated
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from datetime import datetime


# ==================== Copilot Message Models ====================

class CopilotUserMessage(BaseModel):
    """Copilot用户消息"""
    role: Literal["user"] = "user"
    content: str


class CopilotAssistantMessage(BaseModel):
    """Copilot助手消息"""
    role: Literal["assistant"] = "assistant"
    content: str


CopilotMessage = Union[CopilotUserMessage, CopilotAssistantMessage]


# ==================== Copilot Context Models ====================

class CopilotChatContextAgent(BaseModel):
    """智能体上下文"""
    type: Literal["agent"] = "agent"
    name: str


class CopilotChatContextTool(BaseModel):
    """工具上下文"""
    type: Literal["tool"] = "tool"
    name: str


class CopilotChatContextPrompt(BaseModel):
    """提示词上下文"""
    type: Literal["prompt"] = "prompt"
    name: str


class CopilotChatContextChat(BaseModel):
    """聊天上下文"""
    type: Literal["chat"] = "chat"
    messages: List[Dict[str, Any]]  # 消息列表


CopilotChatContext = Union[
    CopilotChatContextAgent,
    CopilotChatContextTool,
    CopilotChatContextPrompt,
    CopilotChatContextChat,
]


# ==================== Data Source Models ====================

class DataSourceForCopilot(BaseModel):
    """Copilot数据源"""
    id: str
    name: str
    description: str
    data: Dict[str, Any]


# ==================== Copilot API Request/Response Models ====================

class CopilotAPIRequest(BaseModel):
    """Copilot API请求"""
    model_config = ConfigDict(populate_by_name=True)
    
    project_id: Annotated[str, Field(alias="projectId")]
    messages: List[CopilotMessage]
    workflow: Dict[str, Any]  # Workflow对象
    context: Optional[CopilotChatContext] = None
    data_sources: Annotated[Optional[List[DataSourceForCopilot]], Field(default=None, alias="dataSources")]


class CopilotStreamEvent(BaseModel):
    """Copilot流式事件"""
    model_config = ConfigDict(populate_by_name=True)
    
    content: Optional[str] = None
    type: Optional[Literal["tool-call", "tool-result", "error", "done", "action-start"]] = None
    tool_name: Annotated[Optional[str], Field(default=None, alias="toolName")]
    tool_call_id: Annotated[Optional[str], Field(default=None, alias="toolCallId")]
    args: Optional[Dict[str, Any]] = None
    query: Optional[str] = None
    result: Optional[Any] = None
    # action-start事件字段
    action: Annotated[Optional[str], Field(default=None)] = None
    config_type: Annotated[Optional[str], Field(default=None, alias="configType")] = None
    name: Annotated[Optional[str], Field(default=None)] = None


class EditAgentInstructionsRequest(BaseModel):
    """编辑智能体提示词请求"""
    model_config = ConfigDict(populate_by_name=True)
    
    project_id: Annotated[str, Field(alias="projectId")]
    messages: List[CopilotMessage]
    workflow: Dict[str, Any]
    context: Optional[CopilotChatContext] = None


class EditAgentInstructionsResponse(BaseModel):
    """编辑智能体提示词响应"""
    model_config = ConfigDict(populate_by_name=True)
    
    agent_instructions: Annotated[str, Field(alias="agentInstructions")]

