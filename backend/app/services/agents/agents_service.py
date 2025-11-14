"""
Agents运行时服务实现
Agents runtime service implementation using OpenAI Agent SDK Python
"""

from typing import AsyncIterator, List, Optional, Dict, Any
from datetime import datetime
import uuid
import sys
import os

# 禁用OpenAI Agent SDK的tracing功能（避免API key错误）
# tracing功能需要OpenAI官方的API key，而我们使用的是第三方API
os.environ.setdefault('OPENAI_AGENTS_DISABLE_TRACING', '1')

# 解决命名冲突：确保导入openai-agents包而不是本地agents目录
# 在导入前清理可能冲突的路径
_original_path = sys.path.copy()
sys.path = [p for p in sys.path if 'Agent-V3' not in p]

# 导入OpenAI Agent SDK
try:
    from agents import Agent, Runner, Tool, FunctionTool
    from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
except ImportError as e:
    # 恢复原始路径
    sys.path = _original_path
    raise ImportError(f"Failed to import OpenAI Agent SDK: {e}. Please ensure openai-agents is installed: pip install openai-agents")

# 恢复原始路径（保持其他导入正常工作）
sys.path = _original_path

from app.models.schemas import (
    Message,
    Workflow,
    WorkflowAgent,
    WorkflowTool,
    WorkflowPrompt,
    AssistantMessage,
    AssistantMessageWithToolCalls,
    ToolMessage as SchemaToolMessage,
)
from app.core.config import get_settings
from app.services.agents.openai_agent_tools import get_openai_agent_tools_service


class AgentsService:
    """
    Agents运行时服务
    Agents runtime service for executing multi-agent workflows using OpenAI Agent SDK
    """
    
    def __init__(self):
        """初始化Agents服务"""
        self.settings = get_settings()
        self.agent_tools_service = get_openai_agent_tools_service()
        self._agents_cache: Dict[str, Agent] = {}
    
    def _create_openai_model(self, model_name: str):
        """
        创建OpenAI模型配置
        Create OpenAI model configuration with custom base URL
        
        Args:
            model_name: 模型名称
            
        Returns:
            OpenAI模型配置对象
        """
        # 验证模型名称
        if not model_name or not isinstance(model_name, str) or not model_name.strip():
            # 如果模型名称为空，使用默认模型
            model_name = self.settings.effective_agent_model
            print(f"⚠️ 模型名称为空，使用默认模型: {model_name}")
        
        # 创建OpenAI模型配置
        # 注意：openai-agents使用OpenAIChatCompletionsModel，需要AsyncOpenAI客户端
        from openai import AsyncOpenAI
        
        # 创建AsyncOpenAI客户端
        openai_client = AsyncOpenAI(
            api_key=self.settings.llm_api_key,
            base_url=self.settings.llm_base_url,
        )
        
        # 创建OpenAI模型
        # OpenAIChatCompletionsModel接受model和openai_client参数
        print(f"🔧 创建模型配置: {model_name} (base_url: {self.settings.llm_base_url})")
        return OpenAIChatCompletionsModel(
            model=model_name,
            openai_client=openai_client,
        )
    
    def _build_instructions(
        self,
        agent_config: WorkflowAgent,
        workflow: Workflow,
    ) -> str:
        """
        构建智能体指令
        Build agent instructions
        
        Args:
            agent_config: 智能体配置
            workflow: 工作流对象
            
        Returns:
            智能体指令
        """
        instructions = agent_config.instructions or ""
        
        # 添加描述
        if agent_config.description:
            instructions = f"{agent_config.description}\n\n{instructions}"
        
        # 添加示例（如果有）
        if agent_config.examples:
            instructions += f"\n\nExamples:\n{agent_config.examples}"
        
        return instructions
    
    def _parse_mentions(
        self,
        instructions: str,
        workflow: Workflow,
    ) -> List[Dict[str, str]]:
        """
        解析instructions中的mentions（@agent_name, @pipeline_name, @tool_name）
        Parse mentions from instructions
        
        Args:
            instructions: 智能体指令
            workflow: 工作流对象
            
        Returns:
            Mentions列表，每个mention包含type和name
        """
        mentions = []
        
        # 创建所有agent和pipeline的名称集合
        agent_names = {agent.name for agent in workflow.agents if not agent.disabled}
        pipeline_names = {pipeline.name for pipeline in workflow.pipelines}
        tool_names = {tool.name for tool in workflow.tools}
        
        # 解析mentions：支持[@type:name](#mention)格式（与原项目一致）
        import re
        # 匹配[@type:name](#mention)模式，其中type可以是agent、tool、pipeline、prompt、variable
        # 原项目使用：/\[@(tool|prompt|agent|pipeline|variable):([^\]]+)\]\(#mention\)/g
        mention_pattern = r'\[@(tool|prompt|agent|pipeline|variable):([^\]]+)\]\(#mention\)'
        matches = re.findall(mention_pattern, instructions)
        
        for match in matches:
            entity_type_str, entity_name = match
            # variable类型在内部被视为prompt
            entity_type = "prompt" if entity_type_str == "variable" else entity_type_str
            
            # 验证实体是否存在
            if entity_type == "agent":
                if entity_name in agent_names:
                    # 过滤掉pipeline agents（它们不应该被引用）
                    agent = next((a for a in workflow.agents if a.name == entity_name), None)
                    if agent and not agent.disabled:
                        agent_type_str = agent.type.value if hasattr(agent.type, 'value') else str(agent.type)
                        if agent_type_str != "pipeline":
                            mentions.append({"type": "agent", "name": entity_name})
            elif entity_type == "pipeline":
                if entity_name in pipeline_names:
                    mentions.append({"type": "pipeline", "name": entity_name})
            elif entity_type == "tool":
                if entity_name in tool_names:
                    mentions.append({"type": "tool", "name": entity_name})
            elif entity_type == "prompt":
                prompt_names = {prompt.name for prompt in workflow.prompts}
                if entity_name in prompt_names:
                    mentions.append({"type": "prompt", "name": entity_name})
        
        return mentions
    
    def _get_handoff_agent_names(
        self,
        agent_config: WorkflowAgent,
        workflow: Workflow,
        all_agents: Dict[str, Agent],
    ) -> List[str]:
        """
        获取handoff agent名称列表
        Get handoff agent names for an agent
        
        Args:
            agent_config: 智能体配置
            workflow: 工作流对象
            all_agents: 所有已创建的agents字典
            
        Returns:
            Handoff agent名称列表
        """
        handoff_agent_names = []
        
        # Pipeline agents不能有直接handoff（除了pipeline内部的handoff）
        # 注意：agent_config.type是AgentType枚举，需要使用.value获取字符串值
        agent_type_str = agent_config.type.value if hasattr(agent_config.type, 'value') else str(agent_config.type)
        if agent_type_str == "pipeline":
            return handoff_agent_names
        
        # 解析instructions中的mentions
        instructions = self._build_instructions(agent_config, workflow)
        mentions = self._parse_mentions(instructions, workflow)
        
        # 提取connected agents和pipelines
        connected_agent_names = [
            m["name"] for m in mentions 
            if m["type"] == "agent" and m["name"] in all_agents
        ]
        connected_pipeline_names = [
            m["name"] for m in mentions 
            if m["type"] == "pipeline"
        ]
        
        # 过滤掉pipeline agents作为直接handoff目标
        valid_agent_names = []
        for agent_name in connected_agent_names:
            target_agent_config = next(
                (a for a in workflow.agents if a.name == agent_name),
                None
            )
            target_agent_type_str = target_agent_config.type.value if hasattr(target_agent_config.type, 'value') else str(target_agent_config.type)
            if target_agent_config and target_agent_type_str != "pipeline":
                valid_agent_names.append(agent_name)
        
        # 对于pipeline mentions，创建handoff到pipeline的第一个agent
        pipeline_first_agents = []
        for pipeline_name in connected_pipeline_names:
            pipeline = next(
                (p for p in workflow.pipelines if p.name == pipeline_name),
                None
            )
            if pipeline and pipeline.agents:
                first_agent_name = pipeline.agents[0]
                if first_agent_name in all_agents:
                    pipeline_first_agents.append(first_agent_name)
        
        # 合并所有handoff目标
        handoff_agent_names = list(set(valid_agent_names + pipeline_first_agents))
        
        return handoff_agent_names
    
    def _create_all_agents(
        self,
        project_id: str,
        workflow: Workflow,
    ) -> Dict[str, Agent]:
        """
        创建所有agents
        Create all agents from workflow
        
        Args:
            project_id: 项目ID
            workflow: 工作流对象
            
        Returns:
            Agents字典，key为agent名称，value为Agent对象
        """
        agents = {}
        
        # 第一遍：创建所有agents（不设置handoffs）
        for agent_config in workflow.agents:
            if agent_config.disabled:
                continue
            
            # 创建工具（已经是OpenAI Agent SDK格式）
            # 传递workflow对象以便从instructions中提取工具mentions
            agent_tools = self.agent_tools_service.create_tools(
                project_id=project_id,
                workflow_tools=workflow.tools,
                agent=agent_config,
                workflow=workflow,
            )
            
            # 构建指令
            instructions = self._build_instructions(agent_config, workflow)
            
            # 获取有效的模型名称
            # 如果智能体没有配置模型或模型名称为空，使用默认模型
            model_name = agent_config.model
            if not model_name or not model_name.strip():
                model_name = self.settings.effective_agent_model
                print(f"⚠️ Agent '{agent_config.name}' 没有配置模型，使用默认模型: {model_name}")
            else:
                print(f"📋 Agent '{agent_config.name}' 使用模型: {model_name}")
            
            # 创建OpenAI模型配置
            model = self._create_openai_model(model_name)
            
            # 创建Agent
            agent = Agent(
                name=agent_config.name,
                instructions=instructions,
                handoff_description=agent_config.description,
                tools=agent_tools,
                handoffs=[],  # 稍后设置
                model=model,
            )
            agents[agent_config.name] = agent
        
        # 第二遍：设置handoffs
        for agent_config in workflow.agents:
            if agent_config.disabled:
                continue
            
            agent = agents[agent_config.name]
            handoff_agent_names = self._get_handoff_agent_names(agent_config, workflow, agents)
            handoff_agents = [agents[name] for name in handoff_agent_names if name in agents]
            agent.handoffs = handoff_agents
        
        return agents
    
    async def stream_response(
        self,
        project_id: str,
        workflow: Workflow,
        messages: List[Message],
    ) -> AsyncIterator[Message]:
        """
        流式响应
        Stream response from agents
        
        Args:
            project_id: 项目ID
            workflow: 工作流对象
            messages: 消息列表
            
        Yields:
            Message对象
        """
        # 如果没有agents，返回空响应
        if not workflow.agents:
            return
        
        # 找到start agent
        start_agent_name = workflow.start_agent_name
        if not start_agent_name:
            # 找到第一个非disabled的agent
            active_agents = [a for a in workflow.agents if not a.disabled]
            if not active_agents:
                return
            start_agent_name = active_agents[0].name
        
        print(f"🚀 开始执行智能体: {start_agent_name}")
        print(f"📊 工作流中共有 {len(workflow.agents)} 个智能体")
        
        # 创建所有agents
        agents = self._create_all_agents(project_id, workflow)
        
        print(f"✅ 成功创建 {len(agents)} 个智能体")
        
        if start_agent_name not in agents:
            yield AssistantMessage(
                role="assistant",
                content=f"错误: 找不到起始agent {start_agent_name}",
                agent_name=start_agent_name,
                response_type="external",
            )
            return
        
        start_agent = agents[start_agent_name]
        
        # 获取用户输入（最后一条用户消息）
        user_input = ""
        for msg in reversed(messages):
            if hasattr(msg, "role") and msg.role == "user":
                if hasattr(msg, "content"):
                    user_input = msg.content
                    break
        
        if not user_input:
            # 如果没有用户消息，返回错误
            yield AssistantMessage(
                role="assistant",
                content="错误: 没有找到用户输入",
                agent_name=start_agent_name,
                response_type="external",
            )
            return
        
        # 执行agent（流式）
        try:
            # 配置OpenAI API
            # 注意：openai-agents需要配置默认的OpenAI客户端
            from agents import set_default_openai_client
            from openai import OpenAI as OpenAIClient
            
            # 创建OpenAI客户端
            # 注意：禁用tracing以避免API key错误（tracing功能需要OpenAI官方的API key）
            openai_client = OpenAIClient(
                api_key=self.settings.llm_api_key,
                base_url=self.settings.llm_base_url,
            )
            
            # 设置默认OpenAI客户端
            # 注意：tracing已在文件开头通过环境变量禁用
            set_default_openai_client(openai_client)
            
            # 使用Runner.run_streamed进行流式响应
            # run_streamed返回RunResultStreaming对象，需要使用stream_events()方法
            result = Runner.run_streamed(
                start_agent,
                user_input,
                max_turns=25,  # 最大轮次
            )
            
            # 流式获取事件
            event_count = 0
            message_count = 0
            accumulated_content = ""  # 累积消息内容
            async for event in result.stream_events():
                event_count += 1
                # 处理事件
                # 根据OpenAI Agent SDK的事件类型进行处理
                event_type = getattr(event, "type", None)
                
                # 调试：记录前20个事件的详细信息，以及每100个事件记录一次
                if event_count <= 20 or event_count % 100 == 0:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"🔍 Event #{event_count}: type={event_type}, event_class={type(event).__name__}")
                    # 打印关键属性值（用于调试）
                    for attr in ["output", "text", "content", "delta", "message", "response"]:
                        if hasattr(event, attr):
                            try:
                                value = getattr(event, attr, None)
                                if value is not None:
                                    logger.info(f"   {attr} = {str(value)[:200]}")  # 只打印前200个字符
                            except:
                                pass
                
                # 尝试多种方式获取输出内容（更全面的提取）
                output = None
                # 优先检查常见的事件类型和属性
                if hasattr(event, "output") and event.output:
                    output = event.output
                elif hasattr(event, "text") and event.text:
                    output = event.text
                elif hasattr(event, "content") and event.content:
                    output = event.content
                elif hasattr(event, "delta"):
                    # 某些事件可能有delta字段
                    delta = event.delta
                    if delta:
                        if hasattr(delta, "content") and delta.content:
                            output = delta.content
                        elif isinstance(delta, str):
                            output = delta
                        elif hasattr(delta, "text") and delta.text:
                            output = delta.text
                
                # 如果output是对象，尝试提取content或text属性
                if output and not isinstance(output, str):
                    if hasattr(output, "content") and output.content:
                        output = output.content
                    elif hasattr(output, "text") and output.text:
                        output = output.text
                    elif hasattr(output, "message") and output.message:
                        # 某些事件可能有message字段
                        msg = output.message
                        if isinstance(msg, str):
                            output = msg
                        elif hasattr(msg, "content") and msg.content:
                            output = msg.content
                        elif hasattr(msg, "text") and msg.text:
                            output = msg.text
                    else:
                        # 尝试转换为字符串
                        try:
                            output = str(output)
                        except:
                            output = None
                
                # 如果还没有output，尝试从事件的所有属性中查找
                if not output:
                    # 检查事件的所有属性，寻找可能包含文本内容的属性
                    for attr_name in dir(event):
                        if attr_name.startswith('_') or attr_name in ['type', 'delta']:
                            continue
                        try:
                            attr_value = getattr(event, attr_name, None)
                            if attr_value and not callable(attr_value):
                                # 如果是字符串且长度合理，可能是内容
                                if isinstance(attr_value, str) and len(attr_value) > 10:
                                    output = attr_value
                                    break
                                # 如果是对象，尝试提取content或text
                                elif hasattr(attr_value, "content") and attr_value.content:
                                    output = attr_value.content
                                    break
                                elif hasattr(attr_value, "text") and attr_value.text:
                                    output = attr_value.text
                                    break
                        except:
                            continue
                
                # 处理agent输出事件 - 扩展事件类型匹配
                # 添加更多可能的事件类型
                # 注意：OpenAI Agent SDK可能使用不同的事件类型名称
                message_content = None
                
                # 扩展事件类型列表，包括更多可能的事件类型
                message_event_types = [
                    "agent_output", "agent_span", "generation_span", "text", "text_delta", 
                    "message", "message_delta", "span", "run", "run_span", "agent.message", 
                    "agent.text", "completion", "completion_delta", "response", "response_delta",
                    "chunk", "chunk_delta", "output", "output_delta", "generation", "generation_delta"
                ]
                
                if event_type in message_event_types:
                    if output:
                        message_content = str(output)
                    elif event_type in ["text", "text_delta", "message", "message_delta", "completion", "completion_delta"]:
                        # 对于文本事件，即使没有output字段，也尝试从事件本身获取
                        if hasattr(event, "text") and event.text:
                            message_content = str(event.text)
                        elif hasattr(event, "content") and event.content:
                            message_content = str(event.content)
                        elif hasattr(event, "message") and event.message:
                            msg = event.message
                            if isinstance(msg, str):
                                message_content = msg
                            elif hasattr(msg, "content") and msg.content:
                                message_content = str(msg.content)
                            elif hasattr(msg, "text") and msg.text:
                                message_content = str(msg.text)
                
                # 如果事件类型未知但output有值，也尝试作为消息内容
                if not message_content and output and event_type not in ["tool_call", "tool_span", "function_span", "function_call", "tool_result", "tool_output", "function_result", "handoff", "handoff_span"]:
                    message_content = str(output)
                
                # 如果找到了消息内容，累积并输出
                if message_content:
                    accumulated_content += message_content
                    # 对于流式输出，可以立即yield每个片段，或者累积后一次性输出
                    # 这里选择立即输出，以支持流式显示
                    message_count += 1
                    yield AssistantMessage(
                        role="assistant",
                        content=message_content,
                        agent_name=start_agent_name,
                        response_type="external",
                    )
                # 如果没有找到消息内容，尝试从事件的属性中直接获取内容（更宽松的匹配）
                elif not message_content and output:
                    # 如果output有值但message_content没有，说明output可能是有效的
                    accumulated_content += str(output)
                    message_count += 1
                    yield AssistantMessage(
                        role="assistant",
                        content=str(output),
                        agent_name=start_agent_name,
                        response_type="external",
                    )
                # 如果还是没有，尝试从其他属性获取
                elif not message_content and not output and event_type not in ["tool_call", "tool_span", "function_span", "function_call", "tool_result", "tool_output", "function_result", "handoff", "handoff_span"]:
                    # 尝试从常见属性获取内容
                    for attr_name in ["message", "response", "generation", "completion", "answer"]:
                        if hasattr(event, attr_name):
                            attr_value = getattr(event, attr_name)
                            if attr_value:
                                if isinstance(attr_value, str):
                                    output = attr_value
                                elif hasattr(attr_value, "content") and attr_value.content:
                                    output = attr_value.content
                                elif hasattr(attr_value, "text") and attr_value.text:
                                    output = attr_value.text
                                break
                    
                    if output:
                        accumulated_content += str(output)
                        message_count += 1
                        yield AssistantMessage(
                            role="assistant",
                            content=str(output),
                            agent_name=start_agent_name,
                            response_type="external",
                        )
                
                # 处理handoff事件
                elif event_type in ["handoff", "handoff_span"]:
                    target_agent = getattr(event, "target_agent", None) or getattr(event, "agent", None)
                    if target_agent:
                        target_agent_name = getattr(target_agent, "name", None) or str(target_agent)
                        yield AssistantMessage(
                            role="assistant",
                            content=f"Handoff to {target_agent_name}",
                            agent_name=start_agent_name,
                            response_type="external",
                        )
                
                # 处理工具调用事件
                elif event_type in ["tool_call", "tool_span", "function_span", "function_call"]:
                    tool_name = getattr(event, "tool_name", None) or getattr(event, "name", None) or getattr(event, "function_name", None)
                    tool_args = getattr(event, "tool_args", None) or getattr(event, "args", None) or getattr(event, "input", None) or getattr(event, "arguments", None) or {}
                    if tool_name:
                        tool_call_id = str(uuid.uuid4())
                        import json
                        yield AssistantMessageWithToolCalls(
                            role="assistant",
                            content=None,
                            tool_calls=[{
                                "id": tool_call_id,
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": json.dumps(tool_args, ensure_ascii=False) if isinstance(tool_args, dict) else str(tool_args),
                                },
                            }],
                            agent_name=start_agent_name,
                        )
                
                # 处理工具结果事件
                elif event_type in ["tool_result", "tool_output", "function_result"]:
                    tool_result = getattr(event, "tool_result", None) or getattr(event, "output", None) or getattr(event, "result", None)
                    tool_name = getattr(event, "tool_name", None) or getattr(event, "name", None) or "unknown"
                    if tool_result:
                        tool_call_id = str(uuid.uuid4())
                        yield SchemaToolMessage(
                            role="tool",
                            content=str(tool_result),
                            tool_call_id=tool_call_id,
                            tool_name=tool_name,
                        )
                
                # 如果事件有输出但类型未知，尝试直接使用
                elif output:
                    # 未知事件类型但有输出内容，尝试作为消息输出
                    yield AssistantMessage(
                        role="assistant",
                        content=str(output),
                        agent_name=start_agent_name,
                        response_type="external",
                    )
            
            # 如果没有生成任何消息，尝试从累积内容中提取
            print(f"📊 事件统计: 总事件数={event_count}, 生成的消息数={message_count}, 累积内容长度={len(accumulated_content)}")
            
            # 如果累积了内容但没有生成消息，输出累积内容
            if message_count == 0 and accumulated_content:
                print(f"⚠️ 使用累积内容作为消息: {accumulated_content[:200]}")
                yield AssistantMessage(
                    role="assistant",
                    content=accumulated_content,
                    agent_name=start_agent_name,
                    response_type="external",
                )
            elif message_count == 0:
                # 如果确实没有任何消息，输出错误提示
                if event_count == 0:
                    yield AssistantMessage(
                        role="assistant",
                        content="抱歉，我没有收到任何响应事件。请检查配置和日志。",
                        agent_name=start_agent_name,
                        response_type="external",
                    )
                else:
                    # 输出详细的调试信息
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"❌ 收到 {event_count} 个事件但没有生成消息。请检查后端日志中的事件详情。")
                    yield AssistantMessage(
                        role="assistant",
                        content=f"抱歉，我收到了 {event_count} 个事件，但没有生成任何消息。请检查事件类型和日志。事件类型可能不匹配，请查看后端日志获取详细信息。",
                        agent_name=start_agent_name,
                        response_type="external",
                    )
        
        except Exception as e:
            # 错误处理
            import traceback
            error_str = str(e)
            error_details = traceback.format_exc()
            
            # 检查是否是模型不存在的错误
            if "Model does not exist" in error_str or "20012" in error_str:
                # 获取起始智能体的模型配置
                start_agent_config = None
                for agent_config in workflow.agents:
                    if agent_config.name == start_agent_name:
                        start_agent_config = agent_config
                        break
                
                model_name = start_agent_config.model if start_agent_config else "未知"
                error_message = (
                    f"模型配置错误：智能体 '{start_agent_name}' 使用的模型 '{model_name}' 不存在。\n\n"
                    f"请检查：\n"
                    f"1. 模型名称是否正确（当前: {model_name}）\n"
                    f"2. 模型是否在 API 提供商处可用\n"
                    f"3. 建议使用默认模型: {self.settings.effective_agent_model}\n\n"
                    f"原始错误: {error_str}"
                )
            else:
                error_message = f"错误: {error_str}\n\n详细信息:\n{error_details}"
            
            yield AssistantMessage(
                role="assistant",
                content=error_message,
                agent_name=start_agent_name,
                response_type="external",
            )


# 全局Agents服务实例（单例模式）
_agents_service: Optional[AgentsService] = None


def get_agents_service() -> AgentsService:
    """
    获取Agents服务实例（单例）
    Get agents service instance (singleton)
    
    Returns:
        Agents服务实例
    """
    global _agents_service
    
    if _agents_service is None:
        _agents_service = AgentsService()
    
    return _agents_service
