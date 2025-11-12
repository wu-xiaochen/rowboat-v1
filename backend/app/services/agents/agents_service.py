"""
Agents运行时服务实现
Agents runtime service implementation using OpenAI Agent SDK Python
"""

from typing import AsyncIterator, List, Optional, Dict, Any
from datetime import datetime
import uuid
import sys
import os

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
        
        # 简化的mention解析：查找@entity_name模式
        import re
        # 匹配@entity_name模式
        mention_pattern = r'@(\w+)'
        matches = re.findall(mention_pattern, instructions)
        
        for match in matches:
            entity_name = match
            # 检查是否是agent
            if entity_name in agent_names:
                mentions.append({"type": "agent", "name": entity_name})
            # 检查是否是pipeline
            elif entity_name in pipeline_names:
                mentions.append({"type": "pipeline", "name": entity_name})
            # 检查是否是tool
            elif entity_name in tool_names:
                mentions.append({"type": "tool", "name": entity_name})
        
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
            agent_tools = self.agent_tools_service.create_tools(
                project_id=project_id,
                workflow_tools=workflow.tools,
                agent=agent_config,
            )
            
            # 构建指令
            instructions = self._build_instructions(agent_config, workflow)
            
            # 创建OpenAI模型配置
            model = self._create_openai_model(agent_config.model)
            
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
        
        # 创建所有agents
        agents = self._create_all_agents(project_id, workflow)
        
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
            openai_client = OpenAIClient(
                api_key=self.settings.llm_api_key,
                base_url=self.settings.llm_base_url,
            )
            
            # 设置默认OpenAI客户端
            set_default_openai_client(openai_client)
            
            # 使用Runner.run_streamed进行流式响应
            # run_streamed返回RunResultStreaming对象，需要使用stream_events()方法
            result = Runner.run_streamed(
                start_agent,
                user_input,
                max_turns=25,  # 最大轮次
            )
            
            # 流式获取事件
            async for event in result.stream_events():
                # 处理事件
                # 根据OpenAI Agent SDK的事件类型进行处理
                event_type = getattr(event, "type", None)
                
                # 处理agent输出事件
                if event_type in ["agent_output", "agent_span", "generation_span"]:
                    output = getattr(event, "output", None) or getattr(event, "text", None) or getattr(event, "content", None)
                    if output:
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
                elif event_type in ["tool_call", "tool_span", "function_span"]:
                    tool_name = getattr(event, "tool_name", None) or getattr(event, "name", None)
                    tool_args = getattr(event, "tool_args", None) or getattr(event, "args", None) or getattr(event, "input", None) or {}
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
        
        except Exception as e:
            # 错误处理
            import traceback
            error_details = traceback.format_exc()
            yield AssistantMessage(
                role="assistant",
                content=f"错误: {str(e)}\n\n详细信息:\n{error_details}",
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
