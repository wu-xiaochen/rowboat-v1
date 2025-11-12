"""
OpenAI Agent SDK工具实现
OpenAI Agent SDK tools implementation
"""

from typing import List, Optional, Dict, Any, Callable
import sys

# 解决命名冲突：确保导入openai-agents包而不是本地agents目录
_original_path = sys.path.copy()
sys.path = [p for p in sys.path if 'Agent-V3' not in p]

try:
    from agents import FunctionTool, Tool, function_tool
except ImportError as e:
    sys.path = _original_path
    raise ImportError(f"Failed to import OpenAI Agent SDK: {e}")

# 恢复原始路径
sys.path = _original_path

from app.core.config import get_settings
from app.models.schemas import WorkflowAgent, WorkflowTool
from app.services.composio.composio_service import get_composio_service
from app.services.rag.rag_service import get_rag_service


class OpenAIAgentToolsService:
    """
    OpenAI Agent SDK工具服务
    OpenAI Agent SDK tools service for creating tools for agents
    """
    
    def __init__(self):
        """初始化OpenAI Agent工具服务"""
        self.settings = get_settings()
        self.composio_service = get_composio_service()
        self.rag_service = get_rag_service()
    
    def create_tools(
        self,
        project_id: str,
        workflow_tools: List[WorkflowTool],
        agent: WorkflowAgent,
    ) -> List[Tool]:
        """
        创建工具列表
        Create tools list for an agent
        
        Args:
            project_id: 项目ID
            workflow_tools: 工作流工具列表
            agent: 智能体配置
            
        Returns:
            工具列表（OpenAI Agent SDK Tool对象）
        """
        tools = []
        
        # 创建RAG工具（如果agent配置了RAG数据源）
        if agent.rag_data_sources:
            rag_tool = self._create_rag_tool(
                project_id=project_id,
                agent=agent,
            )
            if rag_tool:
                tools.append(rag_tool)
        
        # 创建工作流工具
        for workflow_tool in workflow_tools:
            tool = self._create_workflow_tool(
                project_id=project_id,
                workflow_tool=workflow_tool,
            )
            if tool:
                tools.append(tool)
        
        return tools
    
    def _create_rag_tool(
        self,
        project_id: str,
        agent: WorkflowAgent,
    ) -> Optional[FunctionTool]:
        """
        创建RAG工具
        Create RAG tool for an agent
        
        Args:
            project_id: 项目ID
            agent: 智能体配置
            
        Returns:
            RAG工具
        """
        if not agent.rag_data_sources:
            return None
        
        # 使用function_tool装饰器创建工具
        @function_tool(
            name_override="rag_search",
            description_override=agent.description or "Search for relevant documents using RAG",
        )
        async def rag_search_func(query: str) -> str:
            """
            搜索相关文档
            Search for relevant documents using RAG
            
            Args:
                query: 搜索查询，描述要搜索的内容
                
            Returns:
                搜索结果（JSON格式），包含title、name、content、docId、sourceId等字段
            """
            results = await self.rag_service.search(
                project_id=project_id,
                query=query,
                source_ids=agent.rag_data_sources or [],
                return_type=agent.rag_return_type,
                k=agent.rag_k,
            )
            
            # 格式化结果
            if not results:
                return "No relevant documents found."
            
            # 将结果转换为字符串
            import json
            results_dict = [
                {
                    "title": r.title,
                    "name": r.name,
                    "content": r.content,
                    "docId": r.doc_id,
                    "sourceId": r.source_id,
                }
                for r in results
            ]
            return json.dumps(results_dict, ensure_ascii=False, indent=2)
        
        return rag_search_func
    
    def _create_workflow_tool(
        self,
        project_id: str,
        workflow_tool: WorkflowTool,
    ) -> Optional[FunctionTool]:
        """
        创建工作流工具
        Create workflow tool
        
        Args:
            project_id: 项目ID
            workflow_tool: 工作流工具配置
            
        Returns:
            工作流工具
        """
        # 如果是mock工具，创建mock工具
        if workflow_tool.mock_tool:
            return self._create_mock_tool(workflow_tool)
        
        # 如果是Composio工具，创建Composio工具
        if workflow_tool.is_composio and workflow_tool.composio_data:
            return self._create_composio_tool(project_id, workflow_tool)
        
        # 如果是webhook工具，创建webhook工具
        if workflow_tool.is_webhook:
            return self._create_webhook_tool(project_id, workflow_tool)
        
        # 其他类型的工具（暂时不支持）
        return None
    
    def _create_mock_tool(self, workflow_tool: WorkflowTool) -> FunctionTool:
        """
        创建Mock工具
        Create mock tool
        
        Args:
            workflow_tool: 工作流工具配置
            
        Returns:
            Mock工具
        """
        # 使用function_tool装饰器创建工具
        @function_tool(
            name_override=workflow_tool.name,
            description_override=workflow_tool.description,
        )
        async def mock_tool_func(**kwargs) -> str:
            """
            Mock工具函数
            Mock tool function
            
            Args:
                **kwargs: 工具参数
                
            Returns:
                Mock响应
            """
            # 暂时返回mock instructions
            return workflow_tool.mock_instructions or "Mock tool executed."
        
        return mock_tool_func
    
    def _create_composio_tool(
        self,
        project_id: str,
        workflow_tool: WorkflowTool,
    ) -> Optional[FunctionTool]:
        """
        创建Composio工具
        Create Composio tool
        
        Args:
            project_id: 项目ID
            workflow_tool: 工作流工具配置
            
        Returns:
            Composio工具
        """
        # TODO: 实现Composio工具调用
        # 这里暂时返回None
        return None
    
    def _create_webhook_tool(
        self,
        project_id: str,
        workflow_tool: WorkflowTool,
    ) -> Optional[FunctionTool]:
        """
        创建Webhook工具
        Create webhook tool
        
        Args:
            project_id: 项目ID
            workflow_tool: 工作流工具配置
            
        Returns:
            Webhook工具
        """
        # TODO: 实现Webhook工具调用
        # 这里暂时返回None
        return None


# 全局OpenAI Agent工具服务实例（单例模式）
_openai_agent_tools_service: Optional[OpenAIAgentToolsService] = None


def get_openai_agent_tools_service() -> OpenAIAgentToolsService:
    """
    获取OpenAI Agent工具服务实例（单例）
    Get OpenAI Agent tools service instance (singleton)
    
    Returns:
        OpenAI Agent工具服务实例
    """
    global _openai_agent_tools_service
    
    if _openai_agent_tools_service is None:
        _openai_agent_tools_service = OpenAIAgentToolsService()
    
    return _openai_agent_tools_service

