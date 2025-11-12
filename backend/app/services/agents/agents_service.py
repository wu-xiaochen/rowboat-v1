"""
Agents运行时服务实现
Agents runtime service implementation using CrewAI
"""

from typing import AsyncIterator, List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.models.schemas import Message, Workflow, WorkflowAgent, WorkflowTool, WorkflowPrompt
from app.core.config import get_settings
from app.services.rag.rag_service import get_rag_service


class AgentsService:
    """
    Agents运行时服务
    Agents runtime service for executing multi-agent workflows
    """
    
    def __init__(self):
        """初始化Agents服务"""
        self.settings = get_settings()
        self.agent_tools_service = get_agent_tools_service()
    
    def _convert_messages(self, messages: List[Message]) -> List[BaseMessage]:
        """
        转换消息格式
        Convert messages to LangChain format
        
        Args:
            messages: 消息列表
            
        Returns:
            LangChain消息列表
        """
        langchain_messages = []
        for msg in messages:
            if msg.role == "system":
                langchain_messages.append(SystemMessage(content=msg.content))
            elif msg.role == "user":
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                # 检查是否有工具调用
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    # 处理工具调用消息
                    # 注意：LangChain的工具调用消息格式可能不同
                    langchain_messages.append(AIMessage(content=msg.content or ""))
                else:
                    langchain_messages.append(AIMessage(content=msg.content))
            elif msg.role == "tool":
                # 处理工具消息
                tool_msg = msg
                langchain_messages.append(
                    ToolMessage(
                        content=tool_msg.content,
                        tool_call_id=tool_msg.tool_call_id,
                    )
                )
        
        return langchain_messages
    
    def _create_agent(
        self,
        project_id: str,
        agent_config: WorkflowAgent,
        workflow: Workflow,
    ) -> AgentExecutor:
        """
        创建Agent
        Create agent from workflow agent config
        
        Args:
            project_id: 项目ID
            agent_config: 智能体配置
            workflow: 工作流对象
            
        Returns:
            AgentExecutor对象
        """
        # 创建工具
        tools = self.agent_tools_service.create_tools(
            project_id=project_id,
            workflow_tools=workflow.tools,
            agent=agent_config,
        )
        
        # 创建LLM
        llm = ChatOpenAI(
            model=agent_config.model,
            base_url=self.settings.llm_base_url,
            api_key=self.settings.llm_api_key,
            temperature=0.7,
            streaming=True,
        )
        
        # 构建系统提示词
        system_prompt = self._build_system_prompt(agent_config, workflow)
        
        # 创建Agent提示词
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # 创建Agent
        agent = create_openai_tools_agent(
            llm=llm,
            tools=tools,
            prompt=prompt,
        )
        
        # 创建AgentExecutor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=25,  # 最大迭代次数
        )
        
        return agent_executor
    
    def _build_system_prompt(
        self,
        agent_config: WorkflowAgent,
        workflow: Workflow,
    ) -> str:
        """
        构建系统提示词
        Build system prompt for agent
        
        Args:
            agent_config: 智能体配置
            workflow: 工作流对象
            
        Returns:
            系统提示词
        """
        # 基础指令
        instructions = agent_config.instructions or ""
        
        # 添加示例（如果有）
        if agent_config.examples:
            instructions += f"\n\nExamples:\n{agent_config.examples}"
        
        # 添加描述
        if agent_config.description:
            instructions = f"{agent_config.description}\n\n{instructions}"
        
        return instructions
    
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
        
        # 找到start agent（如果没有指定，使用第一个agent）
        start_agent_name = workflow.start_agent_name
        if not start_agent_name:
            # 找到第一个非disabled的agent
            active_agents = [a for a in workflow.agents if not a.disabled]
            if not active_agents:
                return
            start_agent_name = active_agents[0].name
        
        # 找到start agent配置
        start_agent_config = None
        for agent in workflow.agents:
            if agent.name == start_agent_name:
                start_agent_config = agent
                break
        
        if not start_agent_config:
            return
        
        # 创建agent
        agent_executor = self._create_agent(
            project_id=project_id,
            agent_config=start_agent_config,
            workflow=workflow,
        )
        
        # 转换消息
        langchain_messages = self._convert_messages(messages)
        
        # 获取用户输入（最后一条用户消息）
        user_input = ""
        if langchain_messages and isinstance(langchain_messages[-1], HumanMessage):
            user_input = langchain_messages[-1].content
        elif langchain_messages:
            # 找到最后一条用户消息
            for msg in reversed(langchain_messages):
                if isinstance(msg, HumanMessage):
                    user_input = msg.content
                    break
        
        # 执行agent（流式）
        try:
            # 使用agent_executor的流式响应
            async for event in agent_executor.astream_events(
                {
                    "input": user_input,
                    "chat_history": langchain_messages[:-1] if len(langchain_messages) > 1 else [],
                },
                version="v2",
            ):
                # 处理不同的事件类型
                event_type = event.get("event")
                
                if event_type == "on_chat_model_stream":
                    # 处理流式文本输出
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        yield AssistantMessage(
                            role="assistant",
                            content=chunk.content,
                            agent_name=start_agent_config.name,
                            response_type="external",
                        )
                
                elif event_type == "on_tool_start":
                    # 处理工具调用开始
                    tool_name = event.get("name", "")
                    tool_input = event.get("data", {}).get("input", {})
                    
                    # 创建工具调用消息
                    tool_call_id = str(uuid.uuid4())
                    yield AssistantMessageWithToolCalls(
                        role="assistant",
                        content=None,
                        tool_calls=[{
                            "id": tool_call_id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(tool_input, ensure_ascii=False),
                            },
                        }],
                        agent_name=start_agent_config.name,
                    )
                
                elif event_type == "on_tool_end":
                    # 处理工具调用结束
                    tool_name = event.get("name", "")
                    tool_output = event.get("data", {}).get("output", "")
                    
                    # 创建工具消息
                    # 注意：需要找到对应的tool_call_id
                    # 这里暂时使用占位符
                    tool_call_id = str(uuid.uuid4())
                    yield SchemaToolMessage(
                        role="tool",
                        content=str(tool_output),
                        tool_call_id=tool_call_id,
                        tool_name=tool_name,
                    )
        
        except Exception as e:
            # 错误处理
            yield AssistantMessage(
                role="assistant",
                content=f"错误: {str(e)}",
                agent_name=start_agent_config.name,
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

