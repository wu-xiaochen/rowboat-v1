"""
Copilot服务实现
Copilot service implementation using LangChain
"""

import json
import asyncio
import uuid
import logging
from typing import AsyncIterator, Dict, List, Optional, Any
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    AIMessage,
    BaseMessage,
    ToolMessage,
)
from langchain_core.messages.tool import ToolCall
from langchain_core.tools import tool, StructuredTool
from pydantic import BaseModel as PydanticBaseModel, Field as PydanticField
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.core.config import get_settings
from app.core.prompt_loader import get_prompt_loader
from app.services.composio.composio_service import get_composio_service
from app.models.copilot_schemas import (
    CopilotMessage,
    CopilotChatContext,
    DataSourceForCopilot,
    CopilotStreamEvent,
    EditAgentInstructionsResponse,
)
from app.models.schemas import Workflow


def _get_tool_call_id(tc):
    """安全获取 tool_call 的 id，支持字典和对象格式"""
    try:
        if isinstance(tc, dict):
            return tc.get('id', '')
        else:
            return getattr(tc, 'id', None) or ''
    except:
        return ''


class CopilotService:
    """
    Copilot服务
    Copilot service for multi-agent system building
    """
    
    def __init__(self):
        """初始化Copilot服务"""
        self.settings = get_settings()
        self.prompt_loader = get_prompt_loader()
        self.composio_service = get_composio_service()
        
        # 初始化LLM（使用有效的模型名称）
        self.llm = ChatOpenAI(
            model=self.settings.effective_copilot_model,
            base_url=self.settings.llm_base_url,
            api_key=self.settings.llm_api_key,
            temperature=0.7,
            streaming=True,
        )
        
        # 初始化编辑智能体LLM（使用有效的模型名称）
        self.edit_agent_llm = ChatOpenAI(
            model=self.settings.effective_copilot_model,
            base_url=self.settings.llm_base_url,
            api_key=self.settings.llm_api_key,
            temperature=0.7,
            streaming=False,
        )
        
        # 初始化工具列表
        self.tools = self._create_tools()
        
        # 创建Agent（如果有工具）
        # 注意：这里暂时不创建AgentExecutor，因为流式响应需要特殊处理
        # 工具调用将在stream_response方法中处理
    
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
    
    def _create_tools(self, workflow: Optional[Dict[str, Any]] = None) -> List[StructuredTool]:
        """
        创建工具列表
        Create tools list
        
        Args:
            workflow: 工作流对象（可选，用于工具搜索时优先使用已有工具）
        
        Returns:
            工具列表
        """
        tools = []
        
        # 如果启用Composio工具，添加工具搜索工具
        if self.settings.use_composio_tools:
            # 定义参数 schema
            class SearchRelevantToolsInput(PydanticBaseModel):
                """搜索相关工具的输入参数"""
                query: str = PydanticField(
                    description="搜索查询，描述需要什么功能的工具。例如：'发送邮件'、'创建GitHub issue'、'搜索日历事件'等。Search query describing what functionality is needed. Example: 'send email', 'create GitHub issue', 'search calendar events', etc."
                )
            
            async def search_relevant_tools_func(query: str) -> str:
                """
                搜索相关工具
                Search for relevant tools based on a query
                
                Args:
                    query: 搜索查询，描述需要什么功能的工具
                    
                Returns:
                    找到的工具配置（JSON格式）
                """
                # 传递workflow以便优先使用已有工具
                return await self.composio_service.search_relevant_tools(query, workflow=workflow)
            
            search_tool = StructuredTool.from_function(
                func=search_relevant_tools_func,
                name="search_relevant_tools",
                description="搜索相关工具。根据查询描述搜索可用的Composio工具。必须提供 'query' 参数，描述需要什么功能的工具。Search for relevant tools based on a query describing what functionality is needed. Must provide 'query' parameter describing what functionality is needed.",
                args_schema=SearchRelevantToolsInput,
            )
            tools.append(search_tool)
        
        return tools
    
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
            agent_model=self.settings.effective_agent_model,
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
        # 初始化已发送的action-start事件集合（用于去重）
        self._sent_actions = set()
        
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
        # 复刻原项目的 streamText 逻辑，支持多轮工具调用迭代
        try:
            # 动态创建工具（传入workflow以便优先使用已有工具）
            tools = self._create_tools(workflow=workflow)
            
            # 如果启用了工具，使用带工具的LLM
            if tools:
                # 绑定工具到LLM
                llm_with_tools = self.llm.bind_tools(tools)
                
                # 使用带工具的LLM进行流式响应
                # 复刻原项目的 maxSteps: 10 逻辑，最多执行10轮工具调用
                max_iterations = 10
                current_messages = full_messages.copy()
                iteration = 0
                tools_searched = False  # 跟踪是否已经搜索过工具
                
                while iteration < max_iterations:
                    iteration += 1
                    print(f"🔄 [DEBUG] 开始迭代 {iteration}/{max_iterations}", flush=True)
                    
                    # 收集当前迭代的响应
                    assistant_message_content = ""
                    tool_calls_in_this_iteration = []
                    assistant_message_chunks = []
                    final_ai_chunk = None
                    
                    # 流式获取LLM响应
                    try:
                        chunk_count = 0
                        async for chunk in llm_with_tools.astream(current_messages):
                            chunk_count += 1
                            assistant_message_chunks.append(chunk)
                            final_ai_chunk = chunk
                            
                            # 调试：打印 chunk 的完整结构（仅前几次）
                            if iteration == 1 and len(assistant_message_chunks) <= 3:
                                try:
                                    chunk_dict = {}
                                    for attr in dir(chunk):
                                        if not attr.startswith('_') and not callable(getattr(chunk, attr, None)):
                                            try:
                                                value = getattr(chunk, attr, None)
                                                # 特别处理 additional_kwargs 和 tool_call_chunks
                                                if attr == 'additional_kwargs' and value:
                                                    chunk_dict[attr] = json.dumps(value, default=str, ensure_ascii=False) if isinstance(value, dict) else str(value)
                                                elif attr == 'tool_call_chunks' and value:
                                                    chunk_dict[attr] = [json.dumps(tcc, default=str, ensure_ascii=False) if isinstance(tcc, dict) else str(tcc) for tcc in value[:3]]  # 只显示前3个
                                                else:
                                                    chunk_dict[attr] = str(value)[:200] if value else None  # 限制长度
                                            except:
                                                pass
                                    print(f"🔍 [DEBUG] chunk 结构 (迭代 {iteration}, 第 {len(assistant_message_chunks)} 个): {json.dumps(chunk_dict, default=str, ensure_ascii=False)[:1000]}", flush=True)
                                except Exception as e:
                                    print(f"⚠️ [DEBUG] 无法序列化 chunk: {e}", flush=True)
                            
                            # 关键：检查 chunk 的 additional_kwargs 中是否有工具调用参数
                            if hasattr(chunk, 'additional_kwargs') and chunk.additional_kwargs:
                                try:
                                    additional_kwargs = chunk.additional_kwargs
                                    if isinstance(additional_kwargs, dict):
                                        # 检查是否有 function_call 或 tool_calls
                                        if 'function_call' in additional_kwargs or 'tool_calls' in additional_kwargs:
                                            print(f"🔍 [DEBUG] chunk additional_kwargs 包含工具调用信息: {json.dumps(additional_kwargs, default=str, ensure_ascii=False)[:500]}", flush=True)
                                except Exception as e:
                                    print(f"⚠️ [DEBUG] 无法检查 additional_kwargs: {e}", flush=True)
                            
                            # 处理文本内容
                            if hasattr(chunk, 'content') and chunk.content:
                                chunk_content = chunk.content
                                assistant_message_content += chunk_content
                                
                                # 检测copilot_change元数据模式，立即发送action-start事件
                                # 检测模式：可能包含"copilot_change"字符串，然后是 // action: ... \n // config_type: ... \n // name: ...
                                # 或者直接是 // action: ... \n // config_type: ... \n // name: ...
                                # 只在第一次检测到时发送事件，避免重复
                                import re
                                # 匹配模式：查找连续的元数据注释
                                # 模式1: copilot_change\n// action: ... \n// config_type: ... \n// name: ...
                                # 模式2: // action: ... \n// config_type: ... \n// name: ...
                                # 注意：需要匹配 // 而不是转义的 //，并且允许中间有换行和空格
                                copilot_metadata_pattern = r'(?:copilot_change\s*\n)?\/\/\s*action:\s*(\w+)(?:\s*\n|\s+)\/\/\s*config_type:\s*(\w+)(?:\s*\n|\s+)\/\/\s*name:\s*([^\n\{]+)'
                                metadata_matches = list(re.finditer(copilot_metadata_pattern, assistant_message_content, re.MULTILINE))
                                
                                if metadata_matches:
                                    # 找到所有匹配的元数据块
                                    for match in metadata_matches:
                                        action = match.group(1).strip()
                                        config_type = match.group(2).strip()
                                        name = match.group(3).strip()
                                        
                                        # 生成唯一key
                                        action_key = f"{action}_{config_type}_{name}"
                                        
                                        # 初始化_sent_actions集合（如果还没有）
                                        if not hasattr(self, '_sent_actions'):
                                            self._sent_actions = set()
                                        
                                        # 如果这个action还没有发送过，发送action-start事件
                                        if action_key not in self._sent_actions:
                                            # 检查是否已经有JSON开始（在name之后）
                                            name_end_pos = match.end()
                                            json_start_pos = assistant_message_content.find('{', name_end_pos)
                                            
                                            # 如果找到了JSON开始（即使JSON还没完整），发送action-start事件
                                            # 这样前端可以立即显示StreamingAction卡片
                                            if json_start_pos != -1:
                                                self._sent_actions.add(action_key)
                                                yield CopilotStreamEvent(
                                                    type="action-start",
                                                    action=action,
                                                    config_type=config_type,
                                                    name=name,
                                                )
                                                print(f"📢 [DEBUG] 发送 action-start 事件: action={action}, config_type={config_type}, name={name}", flush=True)
                                
                                yield CopilotStreamEvent(content=chunk_content)
                        
                        # 流式响应完成后，记录统计信息
                        print(f"📊 [DEBUG] 迭代 {iteration} 流式响应完成，收到 {chunk_count} 个 chunk，assistant_message_content 长度: {len(assistant_message_content)}", flush=True)
                        if assistant_message_content:
                            preview = assistant_message_content[:300]
                            print(f"📝 [DEBUG] 迭代 {iteration} assistant_message_content 预览: {preview}", flush=True)
                        else:
                            print(f"⚠️ [DEBUG] 迭代 {iteration} assistant_message_content 为空", flush=True)
                        
                        # 注意：在流式响应中，tool_calls 可能分散在多个 chunk 中
                            # 参数可能在后续的 chunk 中才出现，所以这里只收集 tool_call 的框架
                            # 完整的 tool_calls 会在流式响应结束后从 final_ai_chunk 中提取
                            
                            # 处理工具调用（流式中的部分信息）
                            # 关键：检查 additional_kwargs 中的工具调用（OpenAI 格式）
                            if hasattr(chunk, 'additional_kwargs') and chunk.additional_kwargs:
                                additional_kwargs = chunk.additional_kwargs
                                if isinstance(additional_kwargs, dict):
                                    # OpenAI 格式：additional_kwargs.function_call 或 additional_kwargs.tool_calls
                                    if 'function_call' in additional_kwargs:
                                        function_call = additional_kwargs.get('function_call', {})
                                        if isinstance(function_call, dict):
                                            function_name = function_call.get('name', '')
                                            arguments_str = function_call.get('arguments', '')
                                            if function_name and arguments_str:
                                                try:
                                                    arguments_dict = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
                                                    print(f"🔍 [DEBUG] 从 additional_kwargs.function_call 提取到工具调用: name={function_name}, arguments={json.dumps(arguments_dict, default=str, ensure_ascii=False)}", flush=True)
                                                    # 添加到 tool_calls_in_this_iteration（但不立即发送事件）
                                                    # 工具调用事件将在流式响应完成后发送，避免在流式响应期间发送
                                                    tool_call_id = f"call_{uuid.uuid4().hex[:8]}"
                                                    tool_calls_in_this_iteration.append({
                                                        'id': tool_call_id,
                                                        'name': function_name,
                                                        'args': arguments_dict,
                                                    })
                                                except Exception as e:
                                                    print(f"⚠️ [DEBUG] 无法解析 additional_kwargs.function_call.arguments: {e}, 值: {arguments_str}", flush=True)
                            
                            # 处理 LangChain 格式的工具调用
                            if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                                for tool_call in chunk.tool_calls:
                                    # 调试：先打印完整的 tool_call 结构（无论类型）
                                    # 使用 print 和 logging 确保输出
                                    try:
                                        if isinstance(tool_call, dict):
                                            tool_call_str = json.dumps(tool_call, default=str, ensure_ascii=False)
                                        else:
                                            # 尝试将对象转换为字典
                                            tool_call_dict = {}
                                            for attr in dir(tool_call):
                                                if not attr.startswith('_'):
                                                    try:
                                                        value = getattr(tool_call, attr, None)
                                                        if not callable(value):
                                                            tool_call_dict[attr] = value
                                                    except:
                                                        pass
                                            tool_call_str = json.dumps(tool_call_dict, default=str, ensure_ascii=False)
                                        # 同时使用 print 和 logging 确保输出
                                        print(f"🔍 [DEBUG] tool_call 完整内容: {tool_call_str}", flush=True)
                                        logging.info(f"🔍 tool_call 完整内容: {tool_call_str}")
                                    except Exception as e:
                                        print(f"⚠️ [DEBUG] 无法序列化 tool_call: {e}, 类型: {type(tool_call)}", flush=True)
                                        logging.warning(f"⚠️ 无法序列化 tool_call: {e}, 类型: {type(tool_call)}")
                                    
                                    # 安全获取工具调用信息
                                    if isinstance(tool_call, dict):
                                        # LangChain 的 tool_call 可能有多种结构：
                                        # 1. 直接结构：{name: str, args: dict, id: str}
                                        # 2. OpenAI 格式：{id: str, type: str, function: {name: str, arguments: str}}
                                        # 3. 其他格式
                                        
                                        tool_name = tool_call.get('name', '')
                                        tool_call_id = tool_call.get('id', '') or tool_call.get('tool_call_id', '')
                                        
                                        # 尝试多种方式获取 args
                                        tool_args = {}
                                        
                                        # 方式1：直接 args 字段（字典）
                                        if 'args' in tool_call and isinstance(tool_call.get('args'), dict):
                                            tool_args = tool_call.get('args', {})
                                        
                                        # 方式2：function.arguments 字段（JSON 字符串）- OpenAI 格式
                                        elif 'function' in tool_call:
                                            function_obj = tool_call.get('function', {})
                                            if isinstance(function_obj, dict):
                                                if 'name' in function_obj and not tool_name:
                                                    tool_name = function_obj.get('name', '')
                                                arguments_str = function_obj.get('arguments', '')
                                                if arguments_str:
                                                    try:
                                                        tool_args = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
                                                    except json.JSONDecodeError:
                                                        logging.warning(f"⚠️ 无法解析 function.arguments JSON: {arguments_str}")
                                                        tool_args = {}
                                        
                                        # 方式3：直接 arguments 字段（字典或字符串）
                                        if not tool_args:
                                            arguments_value = tool_call.get('arguments')
                                            if isinstance(arguments_value, dict):
                                                tool_args = arguments_value
                                            elif isinstance(arguments_value, str):
                                                try:
                                                    tool_args = json.loads(arguments_value)
                                                except json.JSONDecodeError:
                                                    tool_args = {}
                                        
                                        # 方式4：parameters 字段
                                        if not tool_args:
                                            parameters_value = tool_call.get('parameters')
                                            if isinstance(parameters_value, dict):
                                                tool_args = parameters_value
                                            elif isinstance(parameters_value, str):
                                                try:
                                                    tool_args = json.loads(parameters_value)
                                                except json.JSONDecodeError:
                                                    tool_args = {}
                                        
                                        # 方式5：input 字段
                                        if not tool_args:
                                            input_value = tool_call.get('input')
                                            if isinstance(input_value, dict):
                                                tool_args = input_value
                                        
                                        # 调试：记录参数提取结果
                                        if not tool_args or len(tool_args) == 0:
                                            warning_msg = f"⚠️ 工具 '{tool_name}' 的参数为空，尝试的字段: args={tool_call.get('args')}, function={tool_call.get('function')}, arguments={tool_call.get('arguments')}, parameters={tool_call.get('parameters')}, input={tool_call.get('input')}"
                                            print(f"[DEBUG] {warning_msg}", flush=True)
                                            logging.warning(warning_msg)
                                        else:
                                            success_msg = f"✅ 工具 '{tool_name}' 的参数提取成功: {json.dumps(tool_args, default=str, ensure_ascii=False)}"
                                            print(f"[DEBUG] {success_msg}", flush=True)
                                            logging.info(success_msg)
                                    else:
                                        # 处理对象类型的 tool_call
                                        tool_name = getattr(tool_call, 'name', '') or ''
                                        tool_call_id = _get_tool_call_id(tool_call)
                                        
                                        # 尝试多种方式获取 args
                                        tool_args = {}
                                        
                                        # 方式1：直接 args 属性
                                        if hasattr(tool_call, 'args'):
                                            args_value = getattr(tool_call, 'args', None)
                                            if isinstance(args_value, dict):
                                                tool_args = args_value
                                            elif args_value is not None:
                                                tool_args = args_value
                                        
                                        # 方式2：function 属性（OpenAI 格式）
                                        if not tool_args and hasattr(tool_call, 'function'):
                                            function_obj = getattr(tool_call, 'function', None)
                                            if function_obj:
                                                if hasattr(function_obj, 'name') and not tool_name:
                                                    tool_name = getattr(function_obj, 'name', '') or ''
                                                if hasattr(function_obj, 'arguments'):
                                                    arguments_value = getattr(function_obj, 'arguments', None)
                                                    if isinstance(arguments_value, str):
                                                        try:
                                                            tool_args = json.loads(arguments_value)
                                                        except json.JSONDecodeError:
                                                            tool_args = {}
                                                    elif isinstance(arguments_value, dict):
                                                        tool_args = arguments_value
                                        
                                        # 方式3：arguments 属性
                                        if not tool_args and hasattr(tool_call, 'arguments'):
                                            args_value = getattr(tool_call, 'arguments', None)
                                            if isinstance(args_value, dict):
                                                tool_args = args_value
                                            elif isinstance(args_value, str):
                                                try:
                                                    tool_args = json.loads(args_value)
                                                except json.JSONDecodeError:
                                                    tool_args = {}
                                        
                                        # 方式4：parameters 属性
                                        if not tool_args and hasattr(tool_call, 'parameters'):
                                            params_value = getattr(tool_call, 'parameters', None)
                                            if isinstance(params_value, dict):
                                                tool_args = params_value
                                        
                                        # 调试：打印完整的 tool_call 结构
                                        if not tool_args or len(tool_args) == 0:
                                            logging.warning(f"⚠️ 工具 '{tool_name}' 的参数为空，tool_call 类型: {type(tool_call)}, 属性: {[attr for attr in dir(tool_call) if not attr.startswith('_')]}")
                                        else:
                                            logging.info(f"✅ 工具 '{tool_name}' 的参数提取成功: {json.dumps(tool_args, default=str, ensure_ascii=False)}")
                                    
                                    if not tool_name:
                                        continue
                                    
                                    # 确保 tool_call_id 存在
                                    if not tool_call_id:
                                        tool_call_id = f"call_{uuid.uuid4().hex[:8]}"
                                    
                                    # 收集工具调用信息（但不立即发送事件）
                                    # 工具调用事件将在流式响应完成后发送，避免在流式响应期间发送
                                    tool_calls_in_this_iteration.append({
                                        'id': tool_call_id,
                                        'name': tool_name,
                                        'args': tool_args,
                                    })
                    except Exception as stream_error:
                        # 流式响应错误
                        error_str = str(stream_error)
                        yield CopilotStreamEvent(
                            type="error",
                            content=f"错误: {error_str}",
                        )
                        break
                    
                    # 流式响应结束后，从 final_ai_chunk 中提取完整的 tool_calls
                    # 关键：在流式响应中，工具调用的参数可能分散在多个 chunk 中
                    # 需要从最终的 AIMessage 中提取完整的 tool_calls（包含参数）
                    
                    # 调试：打印 final_ai_chunk 的完整结构
                    if final_ai_chunk:
                        try:
                            print(f"🔍 [DEBUG] final_ai_chunk 类型: {type(final_ai_chunk)}", flush=True)
                            print(f"🔍 [DEBUG] final_ai_chunk 是否为 AIMessage: {isinstance(final_ai_chunk, AIMessage)}", flush=True)
                            if isinstance(final_ai_chunk, AIMessage):
                                print(f"🔍 [DEBUG] final_ai_chunk.tool_calls 存在: {hasattr(final_ai_chunk, 'tool_calls')}", flush=True)
                                if hasattr(final_ai_chunk, 'tool_calls'):
                                    print(f"🔍 [DEBUG] final_ai_chunk.tool_calls 值: {final_ai_chunk.tool_calls}", flush=True)
                                    print(f"🔍 [DEBUG] final_ai_chunk.tool_calls 长度: {len(final_ai_chunk.tool_calls) if final_ai_chunk.tool_calls else 0}", flush=True)
                                # 关键：检查 tool_call_chunks（流式响应中的工具调用可能在这里）
                                if hasattr(final_ai_chunk, 'tool_call_chunks'):
                                    print(f"🔍 [DEBUG] final_ai_chunk.tool_call_chunks 存在: True", flush=True)
                                    print(f"🔍 [DEBUG] final_ai_chunk.tool_call_chunks 值: {final_ai_chunk.tool_call_chunks}", flush=True)
                                    print(f"🔍 [DEBUG] final_ai_chunk.tool_call_chunks 长度: {len(final_ai_chunk.tool_call_chunks) if final_ai_chunk.tool_call_chunks else 0}", flush=True)
                                    # 打印每个 tool_call_chunk 的详细信息
                                    if final_ai_chunk.tool_call_chunks:
                                        for i, tcc in enumerate(final_ai_chunk.tool_call_chunks):
                                            try:
                                                if isinstance(tcc, dict):
                                                    tcc_str = json.dumps(tcc, default=str, ensure_ascii=False)
                                                else:
                                                    tcc_dict = {}
                                                    for attr in dir(tcc):
                                                        if not attr.startswith('_') and not callable(getattr(tcc, attr, None)):
                                                            try:
                                                                value = getattr(tcc, attr, None)
                                                                tcc_dict[attr] = value
                                                            except:
                                                                pass
                                                    tcc_str = json.dumps(tcc_dict, default=str, ensure_ascii=False)
                                                print(f"🔍 [DEBUG] tool_call_chunks[{i}]: {tcc_str}", flush=True)
                                            except Exception as e:
                                                print(f"⚠️ [DEBUG] 无法序列化 tool_call_chunks[{i}]: {e}", flush=True)
                            # 打印所有属性
                            print(f"🔍 [DEBUG] final_ai_chunk 所有属性: {[attr for attr in dir(final_ai_chunk) if not attr.startswith('_') and not callable(getattr(final_ai_chunk, attr, None))]}", flush=True)
                        except Exception as e:
                            print(f"⚠️ [DEBUG] 无法检查 final_ai_chunk: {e}", flush=True)
                    
                    # 手动合并所有 chunk 构建完整的 AIMessage
                    # 收集所有 tool_calls 和 tool_call_chunks（可能分散在多个 chunk 中）
                    all_tool_calls = {}
                    all_tool_call_chunks = {}  # 使用 id 作为 key 合并 tool_call_chunks
                    all_additional_kwargs_function_calls = {}  # 合并 additional_kwargs 中的 function_call
                    merged_content = ""
                    for chunk in assistant_message_chunks:
                        if isinstance(chunk, AIMessage):
                            # 合并内容
                            if hasattr(chunk, 'content') and chunk.content:
                                merged_content += chunk.content
                            # 收集 tool_calls（使用 id 作为 key 去重和合并）
                            if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                                for tc in chunk.tool_calls:
                                    tc_id = _get_tool_call_id(tc)
                                    if tc_id and tc_id not in all_tool_calls:
                                        all_tool_calls[tc_id] = tc
                            # 关键：收集 additional_kwargs 中的 tool_calls（OpenAI 格式，参数可能分散在多个 chunk 中）
                            if hasattr(chunk, 'additional_kwargs') and chunk.additional_kwargs:
                                additional_kwargs = chunk.additional_kwargs
                                if isinstance(additional_kwargs, dict):
                                    # OpenAI 格式：additional_kwargs.tool_calls（数组）
                                    if 'tool_calls' in additional_kwargs:
                                        tool_calls = additional_kwargs.get('tool_calls', [])
                                        if isinstance(tool_calls, list):
                                            for tool_call_item in tool_calls:
                                                if isinstance(tool_call_item, dict):
                                                    # 使用 index 或 id 作为 key
                                                    tool_call_index = tool_call_item.get('index', None)
                                                    tool_call_id = tool_call_item.get('id', None)
                                                    function_obj = tool_call_item.get('function', {})
                                                    
                                                    if isinstance(function_obj, dict):
                                                        function_name = function_obj.get('name', '')
                                                        arguments_str = function_obj.get('arguments', '')
                                                        
                                                        # 使用 index 或 id 作为 key（优先使用 id）
                                                        key = tool_call_id if tool_call_id else (f"index_{tool_call_index}" if tool_call_index is not None else None)
                                                        
                                                        if key:
                                                            if key not in all_additional_kwargs_function_calls:
                                                                all_additional_kwargs_function_calls[key] = {
                                                                    'name': function_name,
                                                                    'arguments': '',
                                                                    'index': tool_call_index,
                                                                    'id': tool_call_id,
                                                                }
                                                            # 合并 arguments（可能分散在多个 chunk 中）
                                                            if arguments_str:
                                                                existing_arguments = all_additional_kwargs_function_calls[key]['arguments']
                                                                all_additional_kwargs_function_calls[key]['arguments'] = existing_arguments + arguments_str
                                                                # 如果 name 为空，尝试从后续 chunk 中获取
                                                                if not all_additional_kwargs_function_calls[key]['name'] and function_name:
                                                                    all_additional_kwargs_function_calls[key]['name'] = function_name
                                                                print(f"🔍 [DEBUG] 合并 additional_kwargs.tool_calls[{tool_call_index}]: name={function_name or '未知'}, arguments 长度: {len(all_additional_kwargs_function_calls[key]['arguments'])}, 当前片段: {arguments_str[:50]}", flush=True)
                                    # 兼容旧格式：additional_kwargs.function_call
                                    elif 'function_call' in additional_kwargs:
                                        function_call = additional_kwargs.get('function_call', {})
                                        if isinstance(function_call, dict):
                                            function_name = function_call.get('name', '')
                                            arguments_str = function_call.get('arguments', '')
                                            if function_name:
                                                # 使用 function_name 作为 key（因为可能没有 id）
                                                if function_name not in all_additional_kwargs_function_calls:
                                                    all_additional_kwargs_function_calls[function_name] = {
                                                        'name': function_name,
                                                        'arguments': '',
                                                    }
                                                # 合并 arguments（可能分散在多个 chunk 中）
                                                if arguments_str:
                                                    existing_arguments = all_additional_kwargs_function_calls[function_name]['arguments']
                                                    all_additional_kwargs_function_calls[function_name]['arguments'] = existing_arguments + arguments_str
                                                    print(f"🔍 [DEBUG] 合并 additional_kwargs.function_call: name={function_name}, arguments 长度: {len(all_additional_kwargs_function_calls[function_name]['arguments'])}", flush=True)
                            
                            # 关键：收集 tool_call_chunks（参数可能分散在多个 chunk 中）
                            if hasattr(chunk, 'tool_call_chunks') and chunk.tool_call_chunks:
                                for tcc in chunk.tool_call_chunks:
                                    tcc_id = _get_tool_call_id(tcc)
                                    if tcc_id:
                                        # 提取参数（从多个位置）
                                        new_args = {}
                                        if isinstance(tcc, dict):
                                            new_args = tcc.get('args', {})
                                            # 尝试从 function.arguments 提取参数
                                            if not new_args or new_args == "":
                                                if 'function' in tcc:
                                                    function_obj = tcc.get('function', {})
                                                    if isinstance(function_obj, dict):
                                                        arguments_str = function_obj.get('arguments', '')
                                                        if arguments_str:
                                                            try:
                                                                new_args = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
                                                            except:
                                                                new_args = {}
                                            # 尝试从 additional_kwargs 提取参数
                                            if not new_args or new_args == "":
                                                if 'additional_kwargs' in tcc:
                                                    additional_kwargs = tcc.get('additional_kwargs', {})
                                                    if isinstance(additional_kwargs, dict) and 'function_call' in additional_kwargs:
                                                        function_call = additional_kwargs.get('function_call', {})
                                                        if isinstance(function_call, dict):
                                                            arguments_str = function_call.get('arguments', '')
                                                            if arguments_str:
                                                                try:
                                                                    new_args = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
                                                                except:
                                                                    new_args = {}
                                        else:
                                            # 对象类型
                                            new_args = getattr(tcc, 'args', {}) if hasattr(tcc, 'args') else {}
                                            # 尝试从 function.arguments 提取参数
                                            if not new_args or new_args == "":
                                                if hasattr(tcc, 'function'):
                                                    function_obj = getattr(tcc, 'function', None)
                                                    if function_obj and hasattr(function_obj, 'arguments'):
                                                        arguments_value = getattr(function_obj, 'arguments', None)
                                                        if isinstance(arguments_value, str) and arguments_value:
                                                            try:
                                                                new_args = json.loads(arguments_value)
                                                            except:
                                                                new_args = {}
                                        
                                        # 如果已存在，尝试合并参数
                                        if tcc_id in all_tool_call_chunks:
                                            existing_tcc = all_tool_call_chunks[tcc_id]
                                            if new_args and new_args != "":
                                                if isinstance(existing_tcc, dict):
                                                    existing_args = existing_tcc.get('args', {})
                                                    if isinstance(existing_args, str):
                                                        existing_args = {}
                                                    existing_tcc['args'] = {**existing_args, **new_args}
                                                else:
                                                    if hasattr(existing_tcc, 'args'):
                                                        existing_args = getattr(existing_tcc, 'args', {})
                                                        if isinstance(existing_args, str):
                                                            existing_args = {}
                                                        setattr(existing_tcc, 'args', {**existing_args, **new_args})
                                        else:
                                            # 创建新的 tool_call_chunk，确保 args 是字典
                                            if isinstance(tcc, dict):
                                                tcc_copy = tcc.copy()
                                                tcc_copy['args'] = new_args if new_args else {}
                                                all_tool_call_chunks[tcc_id] = tcc_copy
                                            else:
                                                all_tool_call_chunks[tcc_id] = tcc
                    
                    print(f"🔍 [DEBUG] 合并了 {len(assistant_message_chunks)} 个 chunk，收集到 {len(all_tool_calls)} 个 tool_calls，{len(all_tool_call_chunks)} 个 tool_call_chunks，{len(all_additional_kwargs_function_calls)} 个 additional_kwargs.function_call", flush=True)
                    
                    # 首先尝试从合并的 tool_call_chunks 中提取完整的 tool_calls
                    # 关键：LangChain 在流式响应中，工具调用的参数可能分散在多个 chunk 中
                    complete_tool_calls = []
                    
                    # 优先使用合并后的 additional_kwargs.tool_calls（OpenAI 格式，参数可能分散在多个 chunk 中）
                    # 关键：如果 additional_kwargs.tool_calls 的 name 为 None，尝试从 tool_call_chunks 中获取 name
                    if all_additional_kwargs_function_calls:
                        print(f"🔍 [DEBUG] 从合并的 additional_kwargs.tool_calls 提取 tool_calls，数量: {len(all_additional_kwargs_function_calls)}", flush=True)
                        for key, function_call_info in all_additional_kwargs_function_calls.items():
                            function_name = function_call_info.get('name', '')
                            arguments_str = function_call_info.get('arguments', '')
                            tool_call_id_from_info = function_call_info.get('id')
                            tool_call_index = function_call_info.get('index', 0)
                            
                            # 如果 name 为 None，尝试从 tool_call_chunks 中获取（通过 id 或 index 匹配）
                            if (not function_name or function_name is None) and all_tool_call_chunks:
                                print(f"🔍 [DEBUG] additional_kwargs.tool_calls 的 name 为 None，尝试从 tool_call_chunks 中获取（id={tool_call_id_from_info}, index={tool_call_index}）", flush=True)
                                # 优先通过 id 匹配
                                if tool_call_id_from_info and tool_call_id_from_info in all_tool_call_chunks:
                                    tcc = all_tool_call_chunks[tool_call_id_from_info]
                                    if isinstance(tcc, dict):
                                        function_name = tcc.get('name', '')
                                    else:
                                        function_name = getattr(tcc, 'name', '') or ''
                                    print(f"🔍 [DEBUG] 通过 id 匹配到 tool_call_chunk，name={function_name}", flush=True)
                                else:
                                    # 如果 id 匹配失败，尝试通过 index 匹配（遍历所有 tool_call_chunks）
                                    for tcc_id, tcc in all_tool_call_chunks.items():
                                        tcc_index = None
                                        if isinstance(tcc, dict):
                                            tcc_index = tcc.get('index', None)
                                        else:
                                            tcc_index = getattr(tcc, 'index', None)
                                        if tcc_index == tool_call_index:
                                            if isinstance(tcc, dict):
                                                function_name = tcc.get('name', '')
                                            else:
                                                function_name = getattr(tcc, 'name', '') or ''
                                            tool_call_id_from_info = tcc_id  # 更新 id
                                            print(f"🔍 [DEBUG] 通过 index 匹配到 tool_call_chunk，name={function_name}, id={tcc_id}", flush=True)
                                            break
                            
                            if arguments_str:
                                try:
                                    arguments_dict = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
                                    print(f"🔍 [DEBUG] 从合并的 additional_kwargs.tool_calls 提取到工具调用: name={function_name}, arguments={json.dumps(arguments_dict, default=str, ensure_ascii=False)}", flush=True)
                                    # 确保 function_name 不是 None 或空字符串
                                    if not function_name or function_name is None:
                                        print(f"⚠️ [DEBUG] function_name 为空或 None，跳过此 tool_call", flush=True)
                                        continue
                                    # 使用原有的 id 或生成新的
                                    tool_call_id = tool_call_id_from_info or f"call_{uuid.uuid4().hex[:8]}"
                                    complete_tool_calls.append({
                                        'name': function_name,
                                        'args': arguments_dict,
                                        'id': tool_call_id,
                                    })
                                    print(f"✅ [DEBUG] 从合并的 additional_kwargs.tool_calls 提取到 tool_call: name={function_name}, args={json.dumps(arguments_dict, default=str, ensure_ascii=False)}, id={tool_call_id}", flush=True)
                                except Exception as e:
                                    print(f"⚠️ [DEBUG] 无法解析合并的 additional_kwargs.tool_calls.arguments: {e}, 值: {arguments_str[:200]}", flush=True)
                                    # 如果解析失败，尝试修复 JSON（可能缺少引号等）
                                    try:
                                        # 尝试修复常见的 JSON 格式问题
                                        fixed_arguments = arguments_str.strip()
                                        if not fixed_arguments.startswith('{'):
                                            fixed_arguments = '{' + fixed_arguments
                                        if not fixed_arguments.endswith('}'):
                                            fixed_arguments = fixed_arguments + '}'
                                        arguments_dict = json.loads(fixed_arguments)
                                        print(f"🔧 [DEBUG] 修复 JSON 后成功解析: {json.dumps(arguments_dict, default=str, ensure_ascii=False)}", flush=True)
                                        # 确保 function_name 不是 None 或空字符串
                                        if not function_name or function_name is None:
                                            print(f"⚠️ [DEBUG] function_name 为空或 None，跳过此 tool_call（修复后）", flush=True)
                                            continue
                                        tool_call_id = tool_call_id_from_info or f"call_{uuid.uuid4().hex[:8]}"
                                        complete_tool_calls.append({
                                            'name': function_name,
                                            'args': arguments_dict,
                                            'id': tool_call_id,
                                        })
                                        print(f"✅ [DEBUG] 从合并的 additional_kwargs.tool_calls 提取到 tool_call（修复后）: name={function_name}, args={json.dumps(arguments_dict, default=str, ensure_ascii=False)}, id={tool_call_id}", flush=True)
                                    except Exception as e2:
                                        print(f"❌ [DEBUG] 修复 JSON 后仍无法解析: {e2}, 原始值: {arguments_str}", flush=True)
                    
                    # 如果 additional_kwargs.function_call 中没有，再使用合并后的 tool_call_chunks
                    # 关键：如果 tool_call_chunks 的 args 为空，尝试从 additional_kwargs.tool_calls 中获取 arguments
                    if not complete_tool_calls and all_tool_call_chunks:
                        print(f"🔍 [DEBUG] 从合并的 tool_call_chunks 提取 tool_calls，数量: {len(all_tool_call_chunks)}", flush=True)
                        for tcc_id, tcc in all_tool_call_chunks.items():
                            # 调试：打印完整的 tool_call_chunk
                            try:
                                if isinstance(tcc, dict):
                                    tcc_str = json.dumps(tcc, default=str, ensure_ascii=False)
                                else:
                                    tcc_dict = {}
                                    for attr in dir(tcc):
                                        if not attr.startswith('_') and not callable(getattr(tcc, attr, None)):
                                            try:
                                                value = getattr(tcc, attr, None)
                                                tcc_dict[attr] = value
                                            except:
                                                pass
                                    tcc_str = json.dumps(tcc_dict, default=str, ensure_ascii=False)
                                print(f"🔍 [DEBUG] 合并的 tool_call_chunk (id={tcc_id}): {tcc_str}", flush=True)
                            except Exception as e:
                                print(f"⚠️ [DEBUG] 无法序列化 tool_call_chunk: {e}", flush=True)
                            
                            # 提取工具调用信息
                            if isinstance(tcc, dict):
                                tcc_name = tcc.get('name', '')
                                tcc_args = tcc.get('args', {})
                                tcc_id_from_tcc = tcc.get('id', '') or tcc.get('tool_call_id', '')
                            else:
                                tcc_name = getattr(tcc, 'name', '') or ''
                                tcc_args = getattr(tcc, 'args', {}) if hasattr(tcc, 'args') else {}
                                tcc_id_from_tcc = _get_tool_call_id(tcc)
                            
                            # 关键：确保 args 是字典类型，不是字符串
                            if isinstance(tcc_args, str):
                                if tcc_args == "":
                                    tcc_args = {}
                                else:
                                    # 尝试解析 JSON 字符串
                                    try:
                                        tcc_args = json.loads(tcc_args)
                                    except:
                                        tcc_args = {}
                            elif not isinstance(tcc_args, dict):
                                tcc_args = {}
                            
                            # 如果 args 为空字典或空字符串，尝试从其他字段提取
                            if not tcc_args or len(tcc_args) == 0 or tcc_args == "":
                                if isinstance(tcc, dict):
                                    # 尝试 function.arguments 格式（LangChain 可能将参数存储在 function.arguments 中）
                                    if 'function' in tcc:
                                        function_obj = tcc.get('function', {})
                                        if isinstance(function_obj, dict):
                                            arguments_str = function_obj.get('arguments', '')
                                            if arguments_str:
                                                try:
                                                    tcc_args = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
                                                    print(f"🔍 [DEBUG] 从 function.arguments 提取到参数: {json.dumps(tcc_args, default=str, ensure_ascii=False)}", flush=True)
                                                except Exception as e:
                                                    print(f"⚠️ [DEBUG] 无法解析 function.arguments: {e}, 值: {arguments_str}", flush=True)
                                                    tcc_args = {}
                                    # 尝试 additional_kwargs 格式
                                    if (not tcc_args or len(tcc_args) == 0) and 'additional_kwargs' in tcc:
                                        additional_kwargs = tcc.get('additional_kwargs', {})
                                        if isinstance(additional_kwargs, dict):
                                            if 'function_call' in additional_kwargs:
                                                function_call = additional_kwargs.get('function_call', {})
                                                if isinstance(function_call, dict):
                                                    arguments_str = function_call.get('arguments', '')
                                                    if arguments_str:
                                                        try:
                                                            tcc_args = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
                                                            print(f"🔍 [DEBUG] 从 additional_kwargs.function_call.arguments 提取到参数: {json.dumps(tcc_args, default=str, ensure_ascii=False)}", flush=True)
                                                        except Exception as e:
                                                            print(f"⚠️ [DEBUG] 无法解析 additional_kwargs.function_call.arguments: {e}, 值: {arguments_str}", flush=True)
                                else:
                                    # 尝试从对象属性中提取
                                    if hasattr(tcc, 'function'):
                                        function_obj = getattr(tcc, 'function', None)
                                        if function_obj and hasattr(function_obj, 'arguments'):
                                            arguments_value = getattr(function_obj, 'arguments', None)
                                            if isinstance(arguments_value, str) and arguments_value:
                                                try:
                                                    tcc_args = json.loads(arguments_value)
                                                    print(f"🔍 [DEBUG] 从 function.arguments 属性提取到参数: {json.dumps(tcc_args, default=str, ensure_ascii=False)}", flush=True)
                                                except Exception as e:
                                                    print(f"⚠️ [DEBUG] 无法解析 function.arguments 属性: {e}, 值: {arguments_value}", flush=True)
                                    # 尝试 additional_kwargs 属性
                                    if (not tcc_args or len(tcc_args) == 0) and hasattr(tcc, 'additional_kwargs'):
                                        additional_kwargs = getattr(tcc, 'additional_kwargs', {})
                                        if isinstance(additional_kwargs, dict):
                                            if 'function_call' in additional_kwargs:
                                                function_call = additional_kwargs.get('function_call', {})
                                                if isinstance(function_call, dict):
                                                    arguments_str = function_call.get('arguments', '')
                                                    if arguments_str:
                                                        try:
                                                            tcc_args = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
                                                            print(f"🔍 [DEBUG] 从 additional_kwargs.function_call.arguments 属性提取到参数: {json.dumps(tcc_args, default=str, ensure_ascii=False)}", flush=True)
                                                        except Exception as e:
                                                            print(f"⚠️ [DEBUG] 无法解析 additional_kwargs.function_call.arguments 属性: {e}, 值: {arguments_str}", flush=True)
                            
                            if tcc_name and tcc_name is not None:
                                # 如果 args 为空，尝试从 additional_kwargs.tool_calls 中获取（通过 id 或 index 匹配）
                                if not tcc_args or len(tcc_args) == 0:
                                    print(f"🔍 [DEBUG] tool_call_chunks 的 args 为空，尝试从 additional_kwargs.tool_calls 中获取（id={tcc_id_from_tcc or tcc_id}）", flush=True)
                                    if all_additional_kwargs_function_calls:
                                        # 优先通过 id 匹配
                                        matched = False
                                        for key, function_call_info in all_additional_kwargs_function_calls.items():
                                            function_id = function_call_info.get('id')
                                            function_index = function_call_info.get('index', 0)
                                            arguments_str = function_call_info.get('arguments', '')
                                            
                                            # 通过 id 匹配
                                            if tcc_id_from_tcc and function_id == tcc_id_from_tcc:
                                                if arguments_str:
                                                    try:
                                                        tcc_args = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
                                                        print(f"🔍 [DEBUG] 通过 id 匹配到 additional_kwargs.tool_calls，args={json.dumps(tcc_args, default=str, ensure_ascii=False)}", flush=True)
                                                        matched = True
                                                        break
                                                    except:
                                                        pass
                                            # 如果 id 匹配失败，尝试通过 index 匹配
                                            elif not matched:
                                                tcc_index = None
                                                if isinstance(tcc, dict):
                                                    tcc_index = tcc.get('index', None)
                                                else:
                                                    tcc_index = getattr(tcc, 'index', None)
                                                if tcc_index is not None and tcc_index == function_index:
                                                    if arguments_str:
                                                        try:
                                                            tcc_args = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
                                                            print(f"🔍 [DEBUG] 通过 index 匹配到 additional_kwargs.tool_calls，args={json.dumps(tcc_args, default=str, ensure_ascii=False)}", flush=True)
                                                            matched = True
                                                            break
                                                        except:
                                                            pass
                                
                                # 确保 args 是字典类型（不是字符串）
                                if not isinstance(tcc_args, dict):
                                    print(f"⚠️ [DEBUG] tool_call args 不是字典类型: {type(tcc_args)}, 值: {tcc_args}，转换为空字典", flush=True)
                                    tcc_args = {}
                                
                                # 确保 id 不是 None
                                final_tcc_id = tcc_id_from_tcc or tcc_id
                                if not final_tcc_id or final_tcc_id is None:
                                    final_tcc_id = f"call_{uuid.uuid4().hex[:8]}"
                                    print(f"⚠️ [DEBUG] tool_call id 为空或 None，生成新 id: {final_tcc_id}", flush=True)
                                
                                complete_tool_calls.append({
                                    'name': tcc_name,
                                    'args': tcc_args,
                                    'id': final_tcc_id,
                                })
                                print(f"✅ [DEBUG] 从合并的 tool_call_chunks 提取到 tool_call: name={tcc_name}, args={json.dumps(tcc_args, default=str, ensure_ascii=False)}, id={final_tcc_id}", flush=True)
                            else:
                                print(f"⚠️ [DEBUG] tool_call name 为空或 None，跳过: tcc_name={tcc_name}", flush=True)
                        
                        # 如果 tool_call_chunks 中没有，再检查 tool_calls
                        if not complete_tool_calls and hasattr(final_ai_chunk, 'tool_calls') and final_ai_chunk.tool_calls:
                            print(f"🔍 [DEBUG] 从 final_ai_chunk.tool_calls 提取 tool_calls，数量: {len(final_ai_chunk.tool_calls)}", flush=True)
                            for tc in final_ai_chunk.tool_calls:
                                # 调试：打印完整的 tool_call
                                try:
                                    if isinstance(tc, dict):
                                        tc_str = json.dumps(tc, default=str, ensure_ascii=False)
                                    else:
                                        tc_dict = {}
                                        for attr in dir(tc):
                                            if not attr.startswith('_') and not callable(getattr(tc, attr, None)):
                                                try:
                                                    value = getattr(tc, attr, None)
                                                    tc_dict[attr] = value
                                                except:
                                                    pass
                                        tc_str = json.dumps(tc_dict, default=str, ensure_ascii=False)
                                    print(f"🔍 [DEBUG] final_ai_chunk 中的 tool_call: {tc_str}", flush=True)
                                except Exception as e:
                                    print(f"⚠️ [DEBUG] 无法序列化 final_ai_chunk 中的 tool_call: {e}", flush=True)
                                
                            # 调试：打印完整的 tool_call
                            try:
                                if isinstance(tc, dict):
                                    tc_str = json.dumps(tc, default=str, ensure_ascii=False)
                                else:
                                    tc_dict = {}
                                    for attr in dir(tc):
                                        if not attr.startswith('_') and not callable(getattr(tc, attr, None)):
                                            try:
                                                value = getattr(tc, attr, None)
                                                tc_dict[attr] = value
                                            except:
                                                pass
                                    tc_str = json.dumps(tc_dict, default=str, ensure_ascii=False)
                                print(f"🔍 [DEBUG] 合并后的 tool_call (id={tc_id}): {tc_str}", flush=True)
                            except Exception as e:
                                print(f"⚠️ [DEBUG] 无法序列化 tool_call: {e}", flush=True)
                            
                            # 提取工具调用信息
                            if isinstance(tc, dict):
                                tc_name = tc.get('name', '')
                                tc_args = tc.get('args', {})
                                tc_id_from_tc = tc.get('id', '') or tc.get('tool_call_id', '')
                            else:
                                tc_name = getattr(tc, 'name', '') or ''
                                tc_args = getattr(tc, 'args', {}) if hasattr(tc, 'args') else {}
                                tc_id_from_tc = _get_tool_call_id(tc)
                            
                            # 如果 args 为空，尝试从其他字段提取
                            if not tc_args or len(tc_args) == 0:
                                if isinstance(tc, dict):
                                    # 尝试 function.arguments 格式
                                    if 'function' in tc:
                                        function_obj = tc.get('function', {})
                                        if isinstance(function_obj, dict):
                                            arguments_str = function_obj.get('arguments', '')
                                            if arguments_str:
                                                try:
                                                    tc_args = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
                                                except:
                                                    tc_args = {}
                                else:
                                    # 尝试从对象属性中提取
                                    if hasattr(tc, 'function'):
                                        function_obj = getattr(tc, 'function', None)
                                        if function_obj and hasattr(function_obj, 'arguments'):
                                            arguments_value = getattr(function_obj, 'arguments', None)
                                            if isinstance(arguments_value, str):
                                                try:
                                                    tc_args = json.loads(arguments_value)
                                                except:
                                                    tc_args = {}
                            
                            if tc_name and tc_name is not None:
                                # 关键：过滤掉 copilot_change，它不是工具
                                if tc_name == "copilot_change":
                                    print(f"⚠️ [DEBUG] 提取的 tool_call name 是 'copilot_change'，这不是工具，跳过: tc_name={tc_name}", flush=True)
                                    continue
                                
                                # 确保 id 不是 None
                                final_tc_id = tc_id_from_tc or tc_id
                                if not final_tc_id or final_tc_id is None:
                                    final_tc_id = f"call_{uuid.uuid4().hex[:8]}"
                                    print(f"⚠️ [DEBUG] tool_call id 为空或 None，生成新 id: {final_tc_id}", flush=True)
                                
                                complete_tool_calls.append({
                                    'name': tc_name,
                                    'args': tc_args,
                                    'id': final_tc_id,
                                })
                                print(f"✅ [DEBUG] 提取到完整 tool_call: name={tc_name}, args={json.dumps(tc_args, default=str, ensure_ascii=False)}, id={final_tc_id}", flush=True)
                            else:
                                print(f"⚠️ [DEBUG] tool_call name 为空或 None，跳过: tc_name={tc_name}", flush=True)
                    
                    # 检测响应中是否包含问题（询问用户）
                    # 如果包含问题且没有copilot_change块，应该停止迭代等待用户回复
                    question_patterns = [
                        r'您是否希望',
                        r'请告诉我',
                        r'请选择',
                        r'您希望',
                        r'您想要',
                        r'Do you wish',
                        r'Please tell me',
                        r'Please choose',
                        r'Would you like',
                        r'What would you like',
                    ]
                    has_question = any(re.search(pattern, assistant_message_content, re.IGNORECASE) for pattern in question_patterns)
                    has_copilot_change = 'copilot_change' in assistant_message_content or '// action:' in assistant_message_content
                    
                    if has_question and not has_copilot_change and not complete_tool_calls:
                        # 响应包含问题但没有配置更改，应该停止等待用户回复
                        print(f"❓ [DEBUG] 检测到响应包含问题且没有配置更改，停止迭代等待用户回复", flush=True)
                        if final_ai_chunk and isinstance(final_ai_chunk, AIMessage):
                            current_messages.append(final_ai_chunk)
                        else:
                            current_messages.append(AIMessage(content=assistant_message_content))
                        print(f"✅ [DEBUG] 迭代 {iteration} 完成（等待用户回复），退出循环", flush=True)
                        break
                    
                    # 如果没有从 final_ai_chunk 中提取到，使用流式收集的 tool_calls
                    if not complete_tool_calls and tool_calls_in_this_iteration:
                        print(f"⚠️ [DEBUG] 未从 final_ai_chunk 提取到 tool_calls，使用流式收集的 tool_calls（数量: {len(tool_calls_in_this_iteration)}）", flush=True)
                        # 过滤掉 name 为 None、空的 tool_calls，以及 copilot_change（它不是工具）
                        filtered_tool_calls = []
                        for tc in tool_calls_in_this_iteration:
                            tc_name = tc.get('name', '') if isinstance(tc, dict) else getattr(tc, 'name', '')
                            if not tc_name or tc_name is None:
                                print(f"⚠️ [DEBUG] 流式收集的 tool_call name 为空或 None，跳过: {tc}", flush=True)
                                continue
                            # 关键：过滤掉 copilot_change，它不是工具
                            if tc_name == "copilot_change":
                                print(f"⚠️ [DEBUG] 流式收集的 tool_call 是 'copilot_change'，这不是工具，跳过: {tc}", flush=True)
                                continue
                            filtered_tool_calls.append(tc)
                        complete_tool_calls = filtered_tool_calls
                    
                    # 如果没有工具调用，退出循环
                    if not complete_tool_calls:
                        # 添加最终的AIMessage（如果没有工具调用）
                        if assistant_message_chunks:
                            if final_ai_chunk and isinstance(final_ai_chunk, AIMessage):
                                current_messages.append(final_ai_chunk)
                            else:
                                current_messages.append(AIMessage(content=assistant_message_content))
                        print(f"✅ [DEBUG] 迭代 {iteration} 完成，没有工具调用，退出循环。最终 assistant_message_content 长度: {len(assistant_message_content)}", flush=True)
                        if assistant_message_content:
                            print(f"📝 [DEBUG] 最终 assistant_message_content 预览: {assistant_message_content[:300]}", flush=True)
                        break
                    
                    # 构建包含工具调用的AIMessage
                    # 使用 ToolCall 对象构建
                    formatted_tool_calls = []
                    for tool_call_info in complete_tool_calls:
                        # 确保 name 是有效字符串（不能是 None）
                        tc_name = tool_call_info.get('name', '')
                        if not tc_name or tc_name is None:
                            print(f"⚠️ [DEBUG] tool_call name 为空或 None，跳过: {tool_call_info}", flush=True)
                            continue
                        
                        # 确保 id 是有效字符串（不能是 None）
                        tc_id = tool_call_info.get('id', '')
                        if not tc_id or tc_id is None:
                            tc_id = f"call_{uuid.uuid4().hex[:8]}"
                            print(f"⚠️ [DEBUG] tool_call id 为空或 None，生成新 id: {tc_id}", flush=True)
                        
                        # 确保 args 是字典类型（不是字符串）
                        tc_args = tool_call_info.get('args', {})
                        if isinstance(tc_args, str):
                            if tc_args == "":
                                tc_args = {}
                            else:
                                # 尝试解析 JSON 字符串
                                try:
                                    tc_args = json.loads(tc_args)
                                except:
                                    tc_args = {}
                        elif not isinstance(tc_args, dict):
                            tc_args = {}
                        
                        formatted_tool_calls.append(
                            ToolCall(
                                name=tc_name,
                                args=tc_args,
                                id=tc_id,
                            )
                        )
                    
                    # 添加包含工具调用的AIMessage
                    # 确保至少有一个有效的 tool_call
                    if formatted_tool_calls:
                        ai_message_with_tools = AIMessage(
                            content=assistant_message_content or "",
                            tool_calls=formatted_tool_calls
                        )
                        current_messages.append(ai_message_with_tools)
                    else:
                        print(f"⚠️ [DEBUG] 没有有效的 tool_calls，跳过创建 AIMessage with tools", flush=True)
                        # 如果没有有效的工具调用，添加普通的 AIMessage
                        if assistant_message_content:
                            current_messages.append(AIMessage(content=assistant_message_content))
                            print(f"✅ [DEBUG] 添加普通 AIMessage，内容长度: {len(assistant_message_content)}", flush=True)
                            print(f"📝 [DEBUG] 普通 AIMessage 内容预览: {assistant_message_content[:300]}", flush=True)
                        else:
                            print(f"⚠️ [DEBUG] assistant_message_content 为空，没有添加 AIMessage", flush=True)
                        print(f"✅ [DEBUG] 迭代 {iteration} 完成，没有有效的 tool_calls，退出循环", flush=True)
                        break
                    
                    # 执行所有工具调用（使用完整的 tool_calls）
                    # 关键：在开始执行工具调用之前，先发送工具调用事件（通知前端）
                    # 这样前端可以显示"正在搜索工具..."状态
                    # 同时检查是否已经搜索过工具，避免重复搜索
                    tool_messages = []  # 初始化 tool_messages
                    for tool_call_info in complete_tool_calls:
                        tool_name = tool_call_info['name']
                        # 如果已经搜索过工具，且这次又要搜索工具，跳过
                        if tool_name == "search_relevant_tools" and tools_searched:
                            print(f"⚠️ [DEBUG] 工具 search_relevant_tools 已经搜索过，跳过重复调用", flush=True)
                            # 创建一个提示消息，告诉 LLM 工具已经搜索过
                            tool_messages.append(
                                ToolMessage(
                                    content="工具 search_relevant_tools 已经搜索过，请不要重复调用。请使用之前搜索到的工具结果，直接创建代理配置。",
                                    tool_call_id=tool_call_info['id'],
                                )
                            )
                            continue
                        
                        tool_args = tool_call_info['args']
                        tool_call_id = tool_call_info['id']
                        # 发送工具调用开始事件
                        yield CopilotStreamEvent(
                            type="tool-call",
                            tool_name=tool_name,
                            tool_call_id=tool_call_id,
                            args=tool_args,
                            query=tool_args.get("query") if isinstance(tool_args, dict) else None,
                        )
                    for tool_call_info in complete_tool_calls:
                        tool_name = tool_call_info['name']
                        tool_args = tool_call_info['args']
                        tool_call_id = tool_call_info['id']
                        
                        # 如果已经搜索过工具，且这次又要搜索工具，跳过执行
                        if tool_name == "search_relevant_tools" and tools_searched:
                            print(f"⚠️ [DEBUG] 工具 search_relevant_tools 已经搜索过，跳过执行", flush=True)
                            continue
                        
                        try:
                            # 找到对应的工具
                            # 过滤掉不应该被调用的"工具"（如 copilot_change 是代码块标记，不是工具）
                            if tool_name == "copilot_change":
                                logging.warning(f"⚠️ 'copilot_change' 是代码块标记，不是工具，跳过调用")
                                # 创建一个提示消息，告诉 LLM copilot_change 是代码块格式，不是工具
                                tool_messages.append(
                                    ToolMessage(
                                        content="copilot_change 是代码块格式标记（```copilot_change），不是工具。请在响应中直接使用 ```copilot_change 代码块格式输出配置，不要尝试调用它作为工具。",
                                        tool_call_id=tool_call_id,
                                    )
                                )
                                continue
                            
                            found_tool = None
                            for tool in tools:
                                if tool.name == tool_name:
                                    found_tool = tool
                                    break
                            
                            if found_tool:
                                # 使用 StructuredTool 的 invoke 方法，它会自动处理参数验证和转换
                                # 如果 tool_args 为空，检查是否是必需参数缺失
                                if not tool_args or len(tool_args) == 0:
                                    # 检查工具的参数 schema，看是否有必需参数
                                    if hasattr(found_tool, 'args_schema'):
                                        schema = found_tool.args_schema
                                        if hasattr(schema, 'model_fields'):
                                            required_fields = [name for name, field in schema.model_fields.items() if field.is_required()]
                                            if required_fields:
                                                error_msg = f"工具 {tool_name} 缺少必需参数: {', '.join(required_fields)}。请检查 tool_call 的参数提取逻辑。"
                                                logging.error(error_msg)
                                                raise ValueError(error_msg)
                                
                                # 确保 tool_args 是字典类型
                                if not isinstance(tool_args, dict):
                                    logging.warning(f"工具 {tool_name} 的参数不是字典类型: {type(tool_args)}, 值: {tool_args}")
                                    tool_args = {}
                                
                                # 使用工具的 invoke 方法（支持异步）
                                try:
                                    logging.info(f"🔧 调用工具 '{tool_name}'，参数: {json.dumps(tool_args, default=str, ensure_ascii=False)}")
                                    
                                    # 直接调用底层函数，避免 StructuredTool 的包装问题
                                    tool_func = getattr(found_tool, 'func', None) or getattr(found_tool, '_func', None)
                                    if tool_func:
                                        # 直接调用底层异步函数
                                        if asyncio.iscoroutinefunction(tool_func):
                                            tool_result = await tool_func(**tool_args)
                                        else:
                                            tool_result = tool_func(**tool_args)
                                    elif hasattr(found_tool, 'ainvoke'):
                                        # 使用 ainvoke，但要确保结果被正确 await
                                        ainvoke_result = found_tool.ainvoke(tool_args)
                                        # ainvoke 返回协程，必须 await
                                        tool_result = await ainvoke_result
                                    elif hasattr(found_tool, 'invoke'):
                                        tool_result = found_tool.invoke(tool_args)
                                    else:
                                        # 最后的回退：直接调用
                                        raise ValueError(f"工具 '{tool_name}' 没有可用的调用方法")
                                    
                                    # 确保 tool_result 不是协程对象（嵌套协程）
                                    while asyncio.iscoroutine(tool_result):
                                        logging.warning(f"⚠️ 工具 '{tool_name}' 返回的是协程对象（嵌套协程），再次 await")
                                        tool_result = await tool_result
                                    
                                    # 标记工具已搜索（如果是 search_relevant_tools）
                                    if tool_name == "search_relevant_tools":
                                        tools_searched = True
                                        print(f"✅ [DEBUG] 工具 search_relevant_tools 已搜索，标记 tools_searched=True", flush=True)
                                    
                                    logging.info(f"✅ 工具 '{tool_name}' 调用成功")
                                    
                                    # 确保 tool_result 是字符串
                                    if tool_result is None:
                                        tool_result_str = "工具执行完成，但没有返回结果"
                                    else:
                                        if not isinstance(tool_result, str):
                                            tool_result_str = str(tool_result)
                                        else:
                                            tool_result_str = tool_result
                                    
                                    tool_messages.append(
                                        ToolMessage(
                                            content=tool_result_str,
                                            tool_call_id=tool_call_id,
                                        )
                                    )
                                    # 发送工具结果事件
                                    yield CopilotStreamEvent(
                                        type="tool-result",
                                        tool_name=tool_name,
                                        tool_call_id=tool_call_id,
                                        result=tool_result_str,
                                    )
                                except (TypeError, ValueError) as e:
                                    # 参数错误，记录详细信息
                                    error_msg = f"工具调用参数错误: {str(e)}. 工具: {tool_name}, 参数: {tool_args}"
                                    logging.error(error_msg)
                                    raise ValueError(error_msg)
                                except Exception as e:
                                    # 捕获所有异常，包括协程相关错误
                                    error_msg = f"工具调用失败: {str(e)}. 工具: {tool_name}, 参数: {tool_args}"
                                    logging.error(error_msg)
                                    # 不要抛出异常，而是创建错误消息，让LLM知道工具调用失败但可以继续
                                    tool_result_str = f"工具调用失败: {str(e)}。请继续处理用户请求，可以尝试其他方法或直接回答用户的问题。"
                                    tool_messages.append(
                                        ToolMessage(
                                            content=tool_result_str,
                                            tool_call_id=tool_call_id,
                                        )
                                    )
                                    yield CopilotStreamEvent(
                                        type="tool-result",
                                        tool_name=tool_name,
                                        tool_call_id=tool_call_id,
                                        result=tool_result_str,
                                    )
                                    continue  # 继续处理下一个工具调用，而不是抛出异常
                            else:
                                error_msg = f"工具 {tool_name} 未找到"
                                tool_messages.append(
                                    ToolMessage(
                                        content=error_msg,
                                        tool_call_id=tool_call_id,
                                    )
                                )
                                yield CopilotStreamEvent(
                                    type="tool-result",
                                    tool_name=tool_name,
                                    tool_call_id=tool_call_id,
                                    result=error_msg,
                                )
                        except Exception as tool_error:
                            error_msg = f"工具调用错误: {str(tool_error)}"
                            tool_messages.append(
                                ToolMessage(
                                    content=error_msg,
                                    tool_call_id=tool_call_id,
                                )
                            )
                            yield CopilotStreamEvent(
                                type="tool-result",
                                tool_name=tool_name,
                                tool_call_id=tool_call_id,
                                result=error_msg,
                            )
                    
                    # 添加ToolMessage到消息列表，继续下一轮迭代
                    current_messages.extend(tool_messages)
                    print(f"📝 [DEBUG] 工具调用后，继续下一轮迭代（迭代 {iteration}/{max_iterations}），当前消息数量: {len(current_messages)}", flush=True)
                    
            else:
                # 如果没有工具，直接使用LLM流式响应
                async for chunk in self.llm.astream(full_messages):
                    # 处理响应块
                    if hasattr(chunk, 'content') and chunk.content:
                        yield CopilotStreamEvent(content=chunk.content)
        except Exception as e:
            # 错误处理：确保错误事件被正确发送
            import traceback
            error_msg = f"错误: {str(e)}"
            logging.error(f"Copilot stream error: {error_msg}\n{traceback.format_exc()}")
            yield CopilotStreamEvent(
                type="error",
                content=error_msg,
            )
            # 确保流正确结束，不要提前关闭连接
    
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


# 全局Copilot服务实例（单例模式）
_copilot_service: Optional[CopilotService] = None


def get_copilot_service() -> CopilotService:
    """
    获取Copilot服务实例（单例）
    Get Copilot service instance (singleton)
    
    Returns:
        Copilot服务实例
    """
    global _copilot_service
    
    if _copilot_service is None:
        _copilot_service = CopilotService()
    
    return _copilot_service

