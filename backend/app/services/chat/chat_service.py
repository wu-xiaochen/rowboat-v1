"""
聊天服务实现
Chat service implementation
"""

from typing import AsyncIterator, List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.models.schemas import Message, Workflow
from app.models.chat_schemas import (
    Turn,
    TurnEvent,
    MessageTurnEvent,
    ErrorTurnEvent,
    DoneTurnEvent,
    TurnInput,
    ApiReason,
    ChatReason,
)
from app.repositories.projects import ProjectsRepository
from app.repositories.conversations import ConversationsRepository
from app.services.agents.agents_service import get_agents_service


class ChatService:
    """
    聊天服务
    Chat service for handling conversation turns
    """
    
    def __init__(self):
        """初始化聊天服务"""
        self.projects_repo = ProjectsRepository()
        self.conversations_repo = ConversationsRepository()
        self.agents_service = get_agents_service()
        # 保存 settings 引用以便在错误处理中使用
        from app.core.config import get_settings
        self.settings = get_settings()
    
    async def run_turn(
        self,
        project_id: str,
        conversation_id: Optional[str],
        messages: List[Message],
        mock_tools: Optional[Dict[str, str]] = None,
        api_key: Optional[str] = None,
    ) -> AsyncIterator[TurnEvent]:
        """
        执行对话回合
        Run a conversation turn
        
        Args:
            project_id: 项目ID
            conversation_id: 对话ID（可选）
            messages: 消息列表
            mock_tools: Mock工具（可选）
            api_key: API密钥（可选）
            
        Yields:
            TurnEvent对象
        """
        # 获取项目
        project = await self.projects_repo.get_by_id(project_id)
        if not project:
            yield ErrorTurnEvent(
                error=f"项目 {project_id} 不存在",
                is_billing_error=False,
            )
            return
        
        # 获取工作流（使用live_workflow）
        workflow = project.live_workflow
        
        # 如果没有conversation_id，创建新对话
        if not conversation_id:
            # 创建新对话
            from app.models.schemas import Conversation
            
            # 构建reason（API调用）
            # 注意：原项目的Conversation的reason使用Turn的Reason类型（chat/api/job）
            conversation_reason = {"type": "api"}  # API调用使用api类型
            
            # 创建对话数据（原项目create方法接受字典）
            conversation_data = {
                "projectId": project_id,
                "workflow": workflow.model_dump(by_alias=True),
                "reason": conversation_reason,
                "isLiveWorkflow": True,
            }
            
            # 保存对话（Repository的create方法接受字典，返回Conversation对象）
            created_conversation = await self.conversations_repo.create(conversation_data)
            conversation_id = created_conversation.id
        else:
            # 验证对话是否存在
            conversation = await self.conversations_repo.get_by_id(conversation_id)
            if not conversation:
                yield ErrorTurnEvent(
                    error=f"对话 {conversation_id} 不存在",
                    is_billing_error=False,
                )
                return
            
            # 验证对话是否属于该项目
            if conversation.project_id != project_id:
                yield ErrorTurnEvent(
                    error=f"对话 {conversation_id} 不属于项目 {project_id}",
                    is_billing_error=False,
                )
                return
        
        # 构建Turn输入
        turn_input = TurnInput(
            messages=messages,
            mock_tools=mock_tools,
        )
        
        # 构建reason（API调用）
        reason = ApiReason(type="api")
        
        # 生成Turn ID
        turn_id = str(uuid.uuid4())
        
        # 执行对话回合
        try:
            # 收集输出消息
            output_messages: List[Message] = []
            
            # 使用agents服务流式生成响应
            async for message in self.agents_service.stream_response(
                project_id=project_id,
                workflow=workflow,
                messages=messages,
            ):
                # 收集消息
                output_messages.append(message)
                
                # 发送消息事件
                yield MessageTurnEvent(
                    type="message",
                    data=message,
                )
            
            # 创建Turn对象
            now = datetime.now()
            turn = Turn(
                id=turn_id,
                reason=reason,
                input=turn_input,
                output=output_messages,
                error=None,
                is_billing_error=False,
                created_at=now.isoformat(),
                updated_at=None,
            )
            
            # 返回完成事件
            yield DoneTurnEvent(
                type="done",
                conversation_id=conversation_id,
                turn=turn,
            )
            
        except Exception as e:
            # 处理不同类型的错误
            error_message = str(e)
            is_billing_error = False
            
            # 检查是否是模型不存在的错误
            if "Model does not exist" in error_message or "20012" in error_message:
                # 提取模型名称（如果可能）
                error_message = f"模型不存在或配置错误。请检查智能体的模型配置。\n\n" \
                              f"建议：使用有效的模型名称，如 '{self.settings.effective_agent_model}'\n\n" \
                              f"原始错误: {error_message}"
            elif "BadRequestError" in str(type(e).__name__):
                # OpenAI API 错误
                error_message = f"API 请求错误: {error_message}"
            
            # 返回错误事件
            yield ErrorTurnEvent(
                error=error_message,
                is_billing_error=is_billing_error,
            )


# 全局聊天服务实例（单例模式）
_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """
    获取聊天服务实例（单例）
    Get chat service instance (singleton)
    
    Returns:
        聊天服务实例
    """
    global _chat_service
    
    if _chat_service is None:
        _chat_service = ChatService()
    
    return _chat_service

