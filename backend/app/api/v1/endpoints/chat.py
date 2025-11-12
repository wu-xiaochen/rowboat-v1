"""
聊天端点
Chat endpoint
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Header, Request
from fastapi.responses import StreamingResponse
import json
import uuid

from app.api import ResponseModel
from app.api.dependencies import verify_api_key, get_optional_api_key
from app.models.chat_schemas import ChatRequest, ChatResponse, TurnEvent
from app.services.chat.chat_service import get_chat_service

router = APIRouter(prefix="/{project_id}/chat", tags=["Chat"])


async def stream_turn_events(
    project_id: str,
    request: ChatRequest,
    api_key: Optional[str] = None,
) -> StreamingResponse:
    """
    流式响应处理
    Stream turn events
    
    Args:
        project_id: 项目ID
        request: 聊天请求
        api_key: API密钥（可选）
        
    Returns:
        StreamingResponse对象
    """
    chat_service = get_chat_service()
    
    async def generate_events():
        """生成SSE事件"""
        try:
            async for event in chat_service.run_turn(
                project_id=project_id,
                conversation_id=request.conversation_id,
                messages=request.messages,
                mock_tools=request.mock_tools,
                api_key=api_key,
            ):
                # 格式化事件
                event_data = event.model_dump(by_alias=True)
                
                # 发送SSE事件
                yield f"event: {event.type}\n"
                yield f"data: {json.dumps(event_data, ensure_ascii=False, default=str)}\n\n"
            
            # 发送完成事件
            yield "event: done\n"
            yield "data: {}\n\n"
            
        except Exception as e:
            # 发送错误事件
            error_event = {
                "type": "error",
                "error": str(e),
                "isBillingError": False,
            }
            yield f"event: error\n"
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("", response_model=dict)
async def chat(
    project_id: str,
    request: ChatRequest,
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    聊天端点
    Chat endpoint for conversation turns
    
    Args:
        project_id: 项目ID
        request: 聊天请求
        authorization: 授权头（Bearer token）
        
    Returns:
        聊天响应（流式或非流式）
    """
    # 验证API Key（如果提供）
    api_key = None
    if authorization:
        parts = authorization.split(" ")
        if len(parts) == 2 and parts[0].lower() == "bearer":
            api_key = parts[1]
    
    # 如果请求流式响应，返回SSE流
    if request.stream:
        return await stream_turn_events(
            project_id=project_id,
            request=request,
            api_key=api_key,
        )
    
    # 非流式响应
    chat_service = get_chat_service()
    
    # 执行对话回合
    turn = None
    conversation_id = request.conversation_id
    
    try:
        async for event in chat_service.run_turn(
            project_id=project_id,
            conversation_id=request.conversation_id,
            messages=request.messages,
            mock_tools=request.mock_tools,
            api_key=api_key,
        ):
            if event.type == "done":
                turn = event.turn
                conversation_id = event.conversation_id
                break
            elif event.type == "error":
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=event.error,
                )
        
        if turn is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="未找到Turn数据",
            )
        
        # 返回响应
        return ResponseModel.success(
            data=ChatResponse(
                conversation_id=conversation_id,
                turn=turn,
            ).model_dump(by_alias=True),
            message="聊天响应成功",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"聊天处理失败: {str(e)}",
        )

