"""
聊天API数据模型
Chat API data models
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum

from app.models.schemas import Message


# ==================== Turn Models ====================

class ReasonType(str, Enum):
    """原因类型"""
    CHAT = "chat"
    API = "api"
    JOB = "job"


class ChatReason(BaseModel):
    """聊天原因"""
    type: Literal["chat"] = "chat"


class ApiReason(BaseModel):
    """API原因"""
    type: Literal["api"] = "api"


class JobReason(BaseModel):
    """任务原因"""
    type: Literal["job"] = "job"
    job_id: str = Field(alias="jobId")
    
    class Config:
        populate_by_name = True


# Union type for all reason types
Reason = Union[ChatReason, ApiReason, JobReason]


class TurnInput(BaseModel):
    """Turn输入"""
    messages: List[Message]
    mock_tools: Optional[Dict[str, str]] = Field(None, alias="mockTools")
    
    class Config:
        populate_by_name = True


class Turn(BaseModel):
    """Turn模型（API响应格式）"""
    id: str
    reason: Reason
    input: TurnInput
    output: List[Message]
    error: Optional[str] = None
    is_billing_error: Optional[bool] = Field(None, alias="isBillingError")
    created_at: str = Field(alias="createdAt")  # ISO datetime string
    updated_at: Optional[str] = Field(None, alias="updatedAt")  # ISO datetime string
    
    class Config:
        populate_by_name = True


# 注意：Conversation中的Turn模型（存储在turns数组中）与API响应中的Turn模型不同
# Conversation中的Turn模型在schemas.py中定义为：
# class Turn(BaseModel):
#     id: str
#     conversation_id: str = Field(alias="conversationId")
#     messages: List[Message]
#     created_at: datetime = Field(alias="createdAt")
#     updated_at: Optional[datetime] = Field(None, alias="updatedAt")


class TurnEventType(str, Enum):
    """Turn事件类型"""
    MESSAGE = "message"
    ERROR = "error"
    DONE = "done"


class MessageTurnEvent(BaseModel):
    """消息Turn事件"""
    type: Literal["message"] = "message"
    data: Message


class ErrorTurnEvent(BaseModel):
    """错误Turn事件"""
    type: Literal["error"] = "error"
    error: str
    is_billing_error: Optional[bool] = Field(None, alias="isBillingError")
    
    class Config:
        populate_by_name = True


class DoneTurnEvent(BaseModel):
    """完成Turn事件"""
    type: Literal["done"] = "done"
    conversation_id: str = Field(alias="conversationId")
    turn: Turn
    
    class Config:
        populate_by_name = True


# Union type for all turn event types
TurnEvent = Union[MessageTurnEvent, ErrorTurnEvent, DoneTurnEvent]


# ==================== Chat API Request/Response Models ====================

class ChatRequest(BaseModel):
    """聊天请求"""
    messages: List[Message]
    conversation_id: Optional[str] = Field(None, alias="conversationId")
    mock_tools: Optional[Dict[str, str]] = Field(None, alias="mockTools")
    stream: Optional[bool] = False
    
    class Config:
        populate_by_name = True


class ChatResponse(BaseModel):
    """聊天响应（非流式）"""
    conversation_id: str = Field(alias="conversationId")
    turn: Turn
    
    class Config:
        populate_by_name = True

