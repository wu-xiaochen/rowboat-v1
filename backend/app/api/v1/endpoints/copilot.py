"""
Copilot端点
Copilot endpoint for multi-agent system building
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Header, Request
from fastapi.responses import StreamingResponse
import json
import uuid

from app.api import ResponseModel
from app.api.dependencies import verify_api_key, get_optional_api_key
from app.models.copilot_schemas import (
    CopilotAPIRequest,
    CopilotStreamEvent,
    EditAgentInstructionsRequest,
    EditAgentInstructionsResponse,
)
from app.services.copilot.copilot_service import get_copilot_service

router = APIRouter(prefix="/{project_id}/copilot", tags=["Copilot"])


@router.post("/stream")
async def stream_copilot_response(
    project_id: str,
    request: CopilotAPIRequest,
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    流式Copilot响应
    Stream copilot response
    
    Args:
        project_id: 项目ID
        request: Copilot请求
        authorization: 授权头（Bearer token）
        
    Returns:
        StreamingResponse对象（SSE格式）
    """
    # 验证项目ID匹配
    if request.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="项目ID不匹配"
        )
    
    # 获取API Key（如果提供）
    api_key = None
    if authorization:
        parts = authorization.split(" ")
        if len(parts) == 2 and parts[0].lower() == "bearer":
            api_key = parts[1]
    
    copilot_service = get_copilot_service()
    
    async def generate_events():
        """生成SSE事件"""
        try:
            async for event in copilot_service.stream_response(
                project_id=project_id,
                messages=request.messages,
                workflow=request.workflow,
                context=request.context,
                data_sources=request.data_sources,
            ):
                # 格式化事件
                event_data = event.model_dump(by_alias=True, exclude_none=True)
                
                # 根据事件类型发送不同的事件名称
                # 如果没有 type 字段，默认为 'message'
                event_type = event_data.get('type')
                if not event_type and event_data.get('content'):
                    event_type = 'message'
                elif not event_type:
                    event_type = 'message'  # 默认类型
                
                # 发送SSE事件（使用正确的事件类型）
                yield f"event: {event_type}\n"
                yield f"data: {json.dumps(event_data, ensure_ascii=False, default=str)}\n\n"
            
            # 发送完成事件
            yield "event: done\n"
            yield "data: {}\n\n"
            
        except Exception as e:
            # 发送错误事件
            import traceback
            import logging
            error_msg = str(e)
            logging.error(f"Copilot stream endpoint error: {error_msg}\n{traceback.format_exc()}")
            error_event = {
                "type": "error",
                "error": error_msg,
            }
            yield f"event: error\n"
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
            # 确保发送完成事件，让客户端知道流已结束
            yield "event: done\n"
            yield "data: {}\n\n"
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/edit-agent-instructions", response_model=EditAgentInstructionsResponse)
async def edit_agent_instructions(
    project_id: str,
    request: EditAgentInstructionsRequest,
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    获取编辑智能体提示词
    Get edit agent instructions
    
    Args:
        project_id: 项目ID
        request: 编辑智能体请求
        authorization: 授权头（Bearer token）
        
    Returns:
        编辑智能体提示词响应
    """
    # 验证项目ID匹配
    if request.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="项目ID不匹配"
        )
    
    copilot_service = get_copilot_service()
    
    try:
        response = await copilot_service.get_edit_agent_instructions(
            project_id=project_id,
            messages=request.messages,
            workflow=request.workflow,
            context=request.context,
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取编辑智能体提示词失败: {str(e)}"
        )

