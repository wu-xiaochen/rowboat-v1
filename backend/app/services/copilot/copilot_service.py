"""
Copilot服务实现
Copilot service implementation using LangChain
"""

import json
import asyncio
from typing import AsyncIterator, Dict, List, Optional, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langchain_core.tools import tool

from app.core.config import get_settings
from app.core.prompt_loader import get_prompt_loader
from app.models.copilot_schemas import (
    CopilotMessage,
    CopilotChatContext,
    DataSourceForCopilot,
    CopilotStreamEvent,
    EditAgentInstructionsResponse,
)
from app.models.schemas import Workflow




class CopilotService:
    """
    Copilot服务
    Copilot service for multi-agent system building
    """
    
    def __init__(self):
        """初始化Copilot服务"""
        self.settings = get_settings()
        self.prompt_loader = get_prompt_loader()
        
        # 初始化LLM
        self.llm = ChatOpenAI(
            model=self.settings.copilot_model,
            base_url=self.settings.llm_base_url,
            api_key=self.settings.llm_api_key,
            temperature=0.7,
            streaming=True,
        )
        
        # 初始化编辑智能体LLM
        self.edit_agent_llm = ChatOpenAI(
            model=self.settings.copilot_model,
            base_url=self.settings.llm_base_url,
            api_key=self.settings.llm_api_key,
            temperature=0.7,
            streaming=False,
        )
    
    def _get_context_prompt(self, context: Optional[CopilotChatContext]) -> str:
        """
        获取上下文提示词
        Get context prompt
        
        Args:
            context: Copilot上下文
            
        Returns:
            上下文提示词
        """
        if context is None:
            return ""
        
        if context.type == "agent":
            return f"**NOTE**:\nThe user is currently working on the following agent:\n{context.name}"
        elif context.type == "tool":
            return f"**NOTE**:\nThe user is currently working on the following tool:\n{context.name}"
        elif context.type == "prompt":
            return f"**NOTE**:The user is currently working on the following prompt:\n{context.name}"
        elif context.type == "chat":
            messages_json = json.dumps(context.messages, ensure_ascii=False, indent=2)
            return f"**NOTE**: The user has just tested the following chat using the workflow above and has provided feedback / question below this json dump:\n```json\n{messages_json}\n```"
        
        return ""
    
    def _get_current_workflow_prompt(self, workflow: Dict[str, Any]) -> str:
        """
        获取当前工作流提示词
        Get current workflow prompt
        
        Args:
            workflow: 工作流对象
            
        Returns:
            工作流提示词
        """
        workflow_json = json.dumps(workflow, ensure_ascii=False, indent=2)
        return f"Context:\n\nThe current workflow config is:\n```json\n{workflow_json}\n```"
    
    def _get_data_sources_prompt(self, data_sources: Optional[List[DataSourceForCopilot]]) -> str:
        """
        获取数据源提示词
        Get data sources prompt
        
        Args:
            data_sources: 数据源列表
            
        Returns:
            数据源提示词
        """
        if not data_sources:
            return ""
        
        simplified_data_sources = [
            {
                "id": ds.id,
                "name": ds.name,
                "description": ds.description,
                "data": ds.data,
            }
            for ds in data_sources
        ]
        data_sources_json = json.dumps(simplified_data_sources, ensure_ascii=False, indent=2)
        return f"**NOTE**:\nThe following data sources are available:\n```json\n{data_sources_json}\n```"
    
    def _convert_messages(self, messages: List[CopilotMessage]) -> List[BaseMessage]:
        """
        转换消息格式
        Convert messages to LangChain format
        
        Args:
            messages: Copilot消息列表
            
        Returns:
            LangChain消息列表
        """
        langchain_messages = []
        for msg in messages:
            if msg.role == "user":
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                langchain_messages.append(AIMessage(content=msg.content))
        
        return langchain_messages
    
    def _build_system_prompt(
        self,
        workflow: Dict[str, Any],
        context: Optional[CopilotChatContext] = None,
        data_sources: Optional[List[DataSourceForCopilot]] = None,
    ) -> str:
        """
        构建系统提示词
        Build system prompt
        
        Args:
            workflow: 工作流对象
            context: Copilot上下文
            data_sources: 数据源列表
            
        Returns:
            系统提示词
        """
        # 将Workflow转换为JSON schema
        workflow_schema = json.dumps(workflow, ensure_ascii=False, indent=2)
        
        # 加载提示词
        system_prompt = self.prompt_loader.build_system_prompt(
            agent_model=self.settings.agent_model,
            workflow_schema=workflow_schema,
            using_rowboat_docs=None,  # 暂时不使用文档
            include_example=True,
        )
        
        return system_prompt
    
    async def stream_response(
        self,
        project_id: str,
        messages: List[CopilotMessage],
        workflow: Dict[str, Any],
        context: Optional[CopilotChatContext] = None,
        data_sources: Optional[List[DataSourceForCopilot]] = None,
    ) -> AsyncIterator[CopilotStreamEvent]:
        """
        流式响应
        Stream response
        
        Args:
            project_id: 项目ID
            messages: 消息列表
            workflow: 工作流对象
            context: Copilot上下文
            data_sources: 数据源列表
            
        Yields:
            CopilotStreamEvent对象
        """
        # 构建系统提示词
        system_prompt = self._build_system_prompt(workflow, context, data_sources)
        
        # 获取上下文提示词
        context_prompt = self._get_context_prompt(context)
        
        # 获取工作流提示词
        workflow_prompt = self._get_current_workflow_prompt(workflow)
        
        # 获取数据源提示词
        data_sources_prompt = self._get_data_sources_prompt(data_sources)
        
        # 转换消息
        langchain_messages = self._convert_messages(messages)
        
        # 更新最后一条用户消息
        if langchain_messages and isinstance(langchain_messages[-1], HumanMessage):
            last_message = langchain_messages[-1]
            last_message.content = f"{workflow_prompt}\n\n{context_prompt}\n\n{data_sources_prompt}\n\nUser: {last_message.content}"
        
        # 构建完整消息列表
        full_messages = [
            SystemMessage(content=system_prompt),
            *langchain_messages,
        ]
        
        # 调用LLM进行流式响应
        try:
            async for chunk in self.llm.astream(full_messages):
                # 处理响应块
                if hasattr(chunk, 'content') and chunk.content:
                    yield CopilotStreamEvent(content=chunk.content)
        except Exception as e:
            # 错误处理
            yield CopilotStreamEvent(content=f"错误: {str(e)}")
    
    async def get_edit_agent_instructions(
        self,
        project_id: str,
        messages: List[CopilotMessage],
        workflow: Dict[str, Any],
        context: Optional[CopilotChatContext] = None,
    ) -> EditAgentInstructionsResponse:
        """
        获取编辑智能体提示词
        Get edit agent instructions
        
        Args:
            project_id: 项目ID
            messages: 消息列表
            workflow: 工作流对象
            context: Copilot上下文
            
        Returns:
            编辑智能体提示词响应
        """
        # 加载编辑智能体提示词
        edit_agent_prompt = self.prompt_loader.get_edit_agent_prompt()
        
        # 获取上下文提示词
        context_prompt = self._get_context_prompt(context)
        
        # 获取工作流提示词
        workflow_prompt = self._get_current_workflow_prompt(workflow)
        
        # 转换消息
        langchain_messages = self._convert_messages(messages)
        
        # 更新最后一条用户消息
        if langchain_messages and isinstance(langchain_messages[-1], HumanMessage):
            last_message = langchain_messages[-1]
            last_message.content = f"{workflow_prompt}\n\n{context_prompt}\n\nUser: {last_message.content}"
        
        # 构建完整消息列表
        full_messages = [
            SystemMessage(content=edit_agent_prompt),
            *langchain_messages,
        ]
        
        # 调用LLM（使用结构化输出）
        response = await self.edit_agent_llm.ainvoke(full_messages)
        
        # 解析响应（假设返回JSON格式）
        try:
            # 尝试解析JSON
            response_content = response.content
            if response_content.startswith("```json"):
                # 提取JSON部分
                json_start = response_content.find("{")
                json_end = response_content.rfind("}") + 1
                response_content = response_content[json_start:json_end]
            
            response_data = json.loads(response_content)
            agent_instructions = response_data.get("agent_instructions", response_content)
        except (json.JSONDecodeError, AttributeError):
            # 如果不是JSON格式，直接使用响应内容
            agent_instructions = response.content if hasattr(response, 'content') else str(response)
        
        return EditAgentInstructionsResponse(agent_instructions=agent_instructions)

