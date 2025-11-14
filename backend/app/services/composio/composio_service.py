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
                # 使用 Composio API 的搜索端点
                # 使用 debug 级别日志，而不是警告（这是正常情况）
                import logging
                logging.debug(f"composio-core库不可用或API不同: {e}，使用HTTP API")
                try:
                    # 尝试使用 Composio API 的搜索端点
                    # 注意：Composio API 可能没有直接的搜索端点，这里尝试通过 toolkits 和 tools 端点来实现
                    # 首先获取所有 toolkits，然后搜索相关工具
                    print(f"🔍 [HTTP API] 开始搜索工具，查询: {query}")
                    toolkit_response = await self.client.get("/toolkits", params={"sort_by": "usage"})
                    print(f"📥 [HTTP API] toolkits 响应状态: {toolkit_response.status_code}")
                    
                    if toolkit_response.status_code == 200:
                        toolkit_data = toolkit_response.json()
                        toolkits = toolkit_data.get("items", [])
                        print(f"📦 [HTTP API] 获取到 {len(toolkits)} 个 toolkits")
                        
                        # 在 toolkits 中搜索匹配的
                        matching_tools = []
                        query_lower = query.lower()
                        
                        # 遍历所有 toolkits，搜索工具
                        # 优化：如果已经找到足够多的工具（>50个），提前返回，避免不必要的搜索
                        max_tools_to_collect = 50  # 最多收集50个工具
                        for i, toolkit in enumerate(toolkits[:10]):  # 限制前10个toolkit以提高性能
                            # 如果已经找到足够多的工具，提前返回
                            if len(matching_tools) >= max_tools_to_collect:
                                print(f"✅ [HTTP API] 已找到 {len(matching_tools)} 个工具（达到上限），提前返回")
                                return matching_tools[:10]
                            
                            toolkit_slug = toolkit.get("slug")
                            if not toolkit_slug:
                                continue
                            
                            print(f"🔍 [HTTP API] 搜索 toolkit {i+1}/10: {toolkit_slug}")
                            # 搜索该 toolkit 中的工具
                            try:
                                tools_response = await self.client.get(
                                    "/tools",
                                    params={
                                        "toolkit_slug": toolkit_slug,
                                        "search": query
                                    },
                                    timeout=10.0  # 10秒超时
                                )
                                
                                print(f"📥 [HTTP API] tools 响应状态 ({toolkit_slug}): {tools_response.status_code}")
                                if tools_response.status_code == 200:
                                    tools_data = tools_response.json()
                                    tools = tools_data.get("items", [])
                                    print(f"📦 [HTTP API] toolkit {toolkit_slug} 找到 {len(tools)} 个工具")
                                    for tool in tools:
                                        matching_tools.append(ComposioToolSuggestion(
                                            toolkit=toolkit.get("name", toolkit_slug),
                                            tool_slug=tool.get("slug", ""),
                                            description=tool.get("description", "")
                                        ))
                                    # 如果找到大量工具（>20个），可以提前返回
                                    if len(matching_tools) > 20:
                                        print(f"✅ [HTTP API] 已找到 {len(matching_tools)} 个工具，提前返回（避免过度搜索）")
                                        return matching_tools[:10]
                                elif tools_response.status_code != 200:
                                    error_text = tools_response.text[:200] if hasattr(tools_response, 'text') else str(tools_response)
                                    print(f"⚠️ [HTTP API] toolkit {toolkit_slug} 搜索失败: {tools_response.status_code}, 错误: {error_text}")
                            except Exception as toolkit_error:
                                # 单个toolkit搜索失败，继续搜索其他toolkit
                                print(f"⚠️ [HTTP API] toolkit {toolkit_slug} 搜索异常: {type(toolkit_error).__name__}: {str(toolkit_error)}")
                                continue  # 继续下一个toolkit
                        
                        # 如果找到工具，返回（即使部分toolkit失败，只要有工具就返回）
                        if matching_tools:
                            print(f"✅ [HTTP API] 找到 {len(matching_tools)} 个匹配的工具（部分toolkit可能失败）")
                            return matching_tools[:10]  # 限制返回数量
                        else:
                            print(f"⚠️ [HTTP API] 未找到匹配的工具")
                    else:
                        error_text = toolkit_response.text[:200] if hasattr(toolkit_response, 'text') else str(toolkit_response)
                        print(f"⚠️ [HTTP API] toolkits 请求失败: {toolkit_response.status_code}, 错误: {error_text}")
                    
                    # 如果没有找到，返回空列表（而不是抛出异常）
                    return []
                except Exception as http_error:
                    import traceback
                    print(f"❌ [HTTP API] Composio HTTP API调用失败: {http_error}")
                    print(f"❌ [HTTP API] 错误详情:\n{traceback.format_exc()}")
                    # 即使出错，也返回已找到的工具（如果有）
                    if matching_tools:
                        print(f"⚠️ [HTTP API] 返回已找到的 {len(matching_tools)} 个工具（尽管出现错误）")
                        return matching_tools[:10]
                    # 如果没有工具，返回空列表，让调用方处理
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

