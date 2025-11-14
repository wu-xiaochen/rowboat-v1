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
            # 优先尝试使用 COMPOSIO_SEARCH_TOOLS 工具（通过HTTP API）
            # 这是Composio提供的专门搜索工具，会返回最相关的工具
            try:
                print(f"🔍 [HTTP API] 使用 COMPOSIO_SEARCH_TOOLS 搜索工具，查询: {query}")
                execute_response = await self.client.post(
                    f"/tools/COMPOSIO_SEARCH_TOOLS/execute",
                    json={
                        "userId": user_id,
                        "arguments": {"use_case": query},
                    },
                    timeout=30.0
                )
                
                if execute_response.status_code == 200:
                    result_data = execute_response.json()
                    
                    # 检查响应格式
                    if isinstance(result_data, dict):
                        # 可能包含 'data' 字段
                        if "data" in result_data:
                            data = result_data["data"]
                        elif "result" in result_data:
                            data = result_data["result"]
                        else:
                            data = result_data
                        
                        # 解析搜索响应
                        if isinstance(data, dict):
                            try:
                                search_response = ComposioToolSearchResponse(**data)
                                # 获取工具列表
                                tools = (
                                    search_response.main_tools or
                                    search_response.results or
                                    []
                                )
                                if tools:
                                    print(f"✅ [HTTP API] COMPOSIO_SEARCH_TOOLS 找到 {len(tools)} 个工具")
                                    return tools
                            except Exception as parse_error:
                                print(f"⚠️ [HTTP API] 解析 COMPOSIO_SEARCH_TOOLS 响应失败: {parse_error}")
                                print(f"⚠️ [HTTP API] 响应数据: {json.dumps(data, indent=2)[:500]}")
                
                print(f"⚠️ [HTTP API] COMPOSIO_SEARCH_TOOLS 返回状态码: {execute_response.status_code}")
                if execute_response.status_code != 200:
                    error_text = execute_response.text[:500] if hasattr(execute_response, 'text') else str(execute_response)
                    print(f"⚠️ [HTTP API] COMPOSIO_SEARCH_TOOLS 错误: {error_text}")
                    
            except Exception as search_tool_error:
                print(f"⚠️ [HTTP API] COMPOSIO_SEARCH_TOOLS 调用失败: {type(search_tool_error).__name__}: {str(search_tool_error)}")
                # 继续尝试其他方法
            
            # 回退方案：尝试使用composio-core库（如果可用）
            try:
                from composio_core import Composio
                composio_client = Composio(api_key=self.api_key)
                
                result = composio_client.tools.execute(
                    tool_name="COMPOSIO_SEARCH_TOOLS",
                    arguments={"use_case": query},
                    entity_id=user_id,
                )
                
                if result and hasattr(result, "successful") and result.successful:
                    data = result.data if hasattr(result, "data") else result
                    if isinstance(data, dict):
                        search_response = ComposioToolSearchResponse(**data)
                        tools = (
                            search_response.main_tools or
                            search_response.results or
                            []
                        )
                        if tools:
                            print(f"✅ [composio-core] 找到 {len(tools)} 个工具")
                            return tools
                    
            except (ImportError, AttributeError, TypeError) as e:
                print(f"⚠️ [composio-core] 库不可用或API不同: {e}")
            
            # 最后回退方案：遍历toolkits搜索（完整搜索，不提前返回）
            print(f"🔍 [HTTP API] 回退到遍历toolkits搜索，查询: {query}")
            try:
                toolkit_response = await self.client.get("/toolkits", params={"sort_by": "usage"})
                
                if toolkit_response.status_code == 200:
                    toolkit_data = toolkit_response.json()
                    toolkits = toolkit_data.get("items", [])
                    print(f"📦 [HTTP API] 获取到 {len(toolkits)} 个 toolkits，开始完整搜索")
                    
                    matching_tools = []
                    query_lower = query.lower()
                    
                    # 完整搜索所有toolkits，不提前返回
                    # 但限制搜索的toolkit数量以避免超时（最多搜索前30个）
                    max_toolkits_to_search = 30
                    for i, toolkit in enumerate(toolkits[:max_toolkits_to_search]):
                        toolkit_slug = toolkit.get("slug")
                        if not toolkit_slug:
                            continue
                        
                        print(f"🔍 [HTTP API] 搜索 toolkit {i+1}/{min(len(toolkits), max_toolkits_to_search)}: {toolkit_slug}")
                        try:
                            tools_response = await self.client.get(
                                "/tools",
                                params={
                                    "toolkit_slug": toolkit_slug,
                                    "search": query
                                },
                                timeout=10.0
                            )
                            
                            if tools_response.status_code == 200:
                                tools_data = tools_response.json()
                                tools = tools_data.get("items", [])
                                if tools:
                                    print(f"📦 [HTTP API] toolkit {toolkit_slug} 找到 {len(tools)} 个工具")
                                    for tool in tools:
                                        matching_tools.append(ComposioToolSuggestion(
                                            toolkit=toolkit.get("name", toolkit_slug),
                                            tool_slug=tool.get("slug", ""),
                                            description=tool.get("description", "")
                                        ))
                            elif tools_response.status_code != 200:
                                error_text = tools_response.text[:200] if hasattr(tools_response, 'text') else str(tools_response)
                                print(f"⚠️ [HTTP API] toolkit {toolkit_slug} 搜索失败: {tools_response.status_code}")
                        except Exception as toolkit_error:
                            print(f"⚠️ [HTTP API] toolkit {toolkit_slug} 搜索异常: {type(toolkit_error).__name__}")
                            continue
                    
                    if matching_tools:
                        print(f"✅ [HTTP API] 完整搜索完成，找到 {len(matching_tools)} 个匹配的工具")
                        # 返回前20个最相关的工具
                        return matching_tools[:20]
                    else:
                        print(f"⚠️ [HTTP API] 完整搜索未找到匹配的工具")
                else:
                    error_text = toolkit_response.text[:200] if hasattr(toolkit_response, 'text') else str(toolkit_response)
                    print(f"⚠️ [HTTP API] toolkits 请求失败: {toolkit_response.status_code}")
                    
            except Exception as http_error:
                import traceback
                print(f"❌ [HTTP API] 遍历toolkits搜索失败: {http_error}")
                print(f"❌ [HTTP API] 错误详情:\n{traceback.format_exc()}")
            
            # 所有方法都失败，返回空列表
            print(f"❌ [HTTP API] 所有搜索方法都失败，返回空列表")
            return []
            
        except Exception as e:
            import traceback
            print(f"❌ Composio工具搜索失败: {e}")
            print(f"❌ 错误详情:\n{traceback.format_exc()}")
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

