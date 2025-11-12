"""
Composio服务实现
Composio service implementation
"""

import json
import httpx
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from app.core.config import get_settings


class ComposioToolSuggestion(BaseModel):
    """Composio工具建议"""
    toolkit: str
    tool_slug: str
    description: str


class ComposioToolSearchResponse(BaseModel):
    """Composio工具搜索响应"""
    main_tools: Optional[List[ComposioToolSuggestion]] = None
    related_tools: Optional[List[ComposioToolSuggestion]] = None
    results: Optional[List[ComposioToolSuggestion]] = None  # 向后兼容


class ComposioTool(BaseModel):
    """Composio工具"""
    slug: str
    name: str
    description: str
    toolkit: Dict[str, Any]
    input_parameters: Dict[str, Any]
    no_auth: bool = False


class ComposioService:
    """
    Composio服务
    Composio service for tool search and execution
    """
    
    BASE_URL = "https://backend.composio.dev/api/v3"
    
    def __init__(self):
        """初始化Composio服务"""
        self.settings = get_settings()
        self.api_key = self.settings.composio_api_key
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
    
    async def search_tools(self, query: str, user_id: str = "0000-0000-0000") -> List[ComposioToolSuggestion]:
        """
        搜索相关工具
        Search for relevant tools
        
        Args:
            query: 搜索查询
            user_id: 用户ID（默认使用占位符）
            
        Returns:
            工具建议列表
        """
        try:
            # 尝试使用composio-core库（如果可用）
            try:
                from composio_core import Composio
                composio_client = Composio(api_key=self.api_key)
                
                # 使用composio-core库执行工具搜索
                # 注意：composio-core库的API可能不同，需要查看文档
                # 这里先尝试通用的execute方法
                result = composio_client.tools.execute(
                    tool_name="COMPOSIO_SEARCH_TOOLS",
                    arguments={"use_case": query},
                    entity_id=user_id,
                )
                
                if result and hasattr(result, "successful") and result.successful:
                    data = result.data if hasattr(result, "data") else result
                    # 解析响应
                    if isinstance(data, dict):
                        search_response = ComposioToolSearchResponse(**data)
                        # 获取工具列表
                        tools = (
                            search_response.main_tools or
                            search_response.results or
                            []
                        )
                        return tools
                    return []
                else:
                    # 如果失败，返回空列表
                    return []
                    
            except (ImportError, AttributeError, TypeError) as e:
                # 如果composio-core库不可用或API不同，使用HTTP调用
                # 注意：Composio API的搜索端点可能需要根据实际API文档调整
                # 这里暂时返回空列表，后续可以根据实际API文档实现
                print(f"警告: composio-core库不可用或API不同: {e}")
                # TODO: 实现HTTP调用（如果Composio API有搜索端点）
                return []
            
        except Exception as e:
            # 错误处理
            print(f"Composio工具搜索失败: {e}")
            return []
    
    async def get_tool(self, tool_slug: str) -> Optional[ComposioTool]:
        """
        获取工具详情
        Get tool details
        
        Args:
            tool_slug: 工具slug
            
        Returns:
            工具详情，如果不存在则返回None
        """
        try:
            # 获取工具详情
            response = await self.client.get(f"/tools/{tool_slug}")
            
            if response.status_code != 200:
                return None
            
            tool_data = response.json()
            
            # 检查错误响应
            if "error" in tool_data:
                return None
            
            # 获取toolkit信息以计算no_auth
            toolkit_slug = tool_data.get("toolkit", {}).get("slug")
            no_auth = False
            
            if toolkit_slug:
                toolkit_response = await self.client.get(f"/toolkits/{toolkit_slug}")
                if toolkit_response.status_code == 200:
                    toolkit_data = toolkit_response.json()
                    # 计算no_auth
                    no_auth = (
                        "NO_AUTH" in toolkit_data.get("composio_managed_auth_schemes", []) or
                        any(
                            config.get("mode") == "NO_AUTH"
                            for config in toolkit_data.get("auth_config_details", [])
                        ) or
                        False
                    )
            
            tool_data["no_auth"] = no_auth
            
            return ComposioTool(**tool_data)
            
        except Exception as e:
            # 错误处理
            print(f"获取Composio工具失败: {e}")
            return None
    
    async def get_tools(self, tool_slugs: List[str]) -> List[ComposioTool]:
        """
        批量获取工具详情
        Get multiple tool details
        
        Args:
            tool_slugs: 工具slug列表
            
        Returns:
            工具详情列表
        """
        tools = []
        for slug in tool_slugs:
            tool = await self.get_tool(slug)
            if tool:
                tools.append(tool)
        return tools
    
    async def search_relevant_tools(self, query: str) -> str:
        """
        搜索相关工具并返回格式化的响应
        Search for relevant tools and return formatted response
        
        Args:
            query: 搜索查询
            
        Returns:
            格式化的工具配置字符串
        """
        # 检查是否启用Composio工具
        if not self.settings.use_composio_tools:
            return "No tools found! (Composio tools disabled)"
        
        # 搜索工具
        tools = await self.search_tools(query)
        
        if not tools:
            return "No tools found!"
        
        # 获取工具详情
        tool_slugs = [tool.tool_slug for tool in tools]
        composio_tools = await self.get_tools(tool_slugs)
        
        if not composio_tools:
            return "No tools found!"
        
        # 转换为WorkflowTool格式
        from app.models.schemas import WorkflowTool, ComposioToolData
        
        workflow_tools = []
        for tool in composio_tools:
            workflow_tool = WorkflowTool(
                name=tool.name,
                description=tool.description,
                parameters={
                    "type": "object",
                    "properties": tool.input_parameters.get("properties", {}),
                    "required": tool.input_parameters.get("required", []),
                },
                is_composio=True,
                composio_data=ComposioToolData(
                    slug=tool.slug,
                    no_auth=tool.no_auth,
                    toolkit_name=tool.toolkit.get("name", ""),
                    toolkit_slug=tool.toolkit.get("slug", ""),
                    logo=tool.toolkit.get("logo", ""),
                ),
            )
            workflow_tools.append(workflow_tool)
        
        # 格式化响应
        tool_configs = [
            f"**{tool.name}**:\n```json\n{json.dumps(tool.model_dump(by_alias=True), indent=2, ensure_ascii=False)}\n```"
            for tool in workflow_tools
        ]
        
        response = f"The following tools were found:\n\n{chr(10).join(tool_configs)}"
        return response
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()


# 全局Composio服务实例（单例模式）
_composio_service: Optional[ComposioService] = None


def get_composio_service() -> ComposioService:
    """
    获取Composio服务实例（单例）
    Get Composio service instance (singleton)
    
    Returns:
        Composio服务实例
    """
    global _composio_service
    
    if _composio_service is None:
        _composio_service = ComposioService()
    
    return _composio_service

