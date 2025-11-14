"""
对话管理端点
Conversations management endpoints
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query

from app.api import ResponseModel
from app.models.schemas import Conversation
from app.repositories.conversations import ConversationsRepository

router = APIRouter(prefix="/{project_id}/conversations", tags=["Conversations"])


@router.get("", response_model=dict)
async def list_conversations(
    project_id: str,
    cursor: Optional[str] = Query(None, description="分页游标"),
    limit: int = Query(50, ge=1, le=50, description="返回的最大记录数（最多50）"),
):
    """
    获取对话列表
    List conversations
    严格复刻原项目：使用_id作为游标，返回ListedConversationItem（只包含部分字段）
    
    Args:
        project_id: 项目ID
        cursor: 分页游标（可选）
        limit: 返回的最大记录数（最多50）
        
    Returns:
        对话列表（分页结果）
    """
    repo = ConversationsRepository()
    
    # 获取对话列表
    result = await repo.list(project_id, cursor=cursor, limit=limit)
    
    # 转换为响应格式
    conversations_data = result["items"]
    
    return ResponseModel.success(
        data={
            "items": conversations_data,
            "nextCursor": result["nextCursor"],
        },
        message="对话列表获取成功"
    )


@router.get("/{conversation_id}", response_model=dict)
async def get_conversation(
    project_id: str,
    conversation_id: str,
):
    """
    获取对话详情
    Get conversation details
    严格复刻原项目：先fetch，然后验证项目归属
    
    Args:
        project_id: 项目ID
        conversation_id: 对话ID
        
    Returns:
        对话详情
    """
    repo = ConversationsRepository()
    
    # 获取对话（原项目先fetch）
    conversation = await repo.fetch(conversation_id)
    
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"对话 {conversation_id} 不存在"
        )
    
    # 验证对话属于该项目
    if conversation.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"对话 {conversation_id} 不存在"
        )
    
    return ResponseModel.success(
        data=conversation.model_dump(by_alias=True),
        message="对话详情获取成功"
    )

