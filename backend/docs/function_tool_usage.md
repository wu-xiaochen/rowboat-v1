# @function_tool 装饰器使用指南

## 概述

`@function_tool` 是 OpenAI Agent SDK Python 版本提供的装饰器，用于将普通 Python 函数转换为 Agent 可用的工具（Tool）。

## 基本用法

### 1. 最简单的用法

```python
from agents import function_tool

@function_tool
async def my_tool(query: str) -> str:
    """
    工具描述
    
    Args:
        query: 查询参数
        
    Returns:
        返回结果
    """
    return f"处理查询: {query}"
```

**说明：**
- 函数名会被用作工具名称（`my_tool`）
- 函数的文档字符串会被用作工具描述
- 函数参数的类型注解会被用来定义工具的参数
- 装饰后的函数返回一个 `FunctionTool` 对象

### 2. 指定工具名称和描述

```python
@function_tool(
    name_override="custom_tool_name",
    description_override="自定义工具描述"
)
async def my_tool(query: str) -> str:
    """
    工具描述（如果提供了description_override，这个描述会被覆盖）
    
    Args:
        query: 查询参数
        
    Returns:
        返回结果
    """
    return f"处理查询: {query}"
```

**说明：**
- `name_override`: 覆盖函数名，指定工具的名称
- `description_override`: 覆盖函数的文档字符串，指定工具的描述

### 3. 当前项目中的实际使用

参考 `backend/app/services/agents/openai_agent_tools.py` 中的实现：

#### RAG工具

```python
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

return rag_search_func  # 返回装饰后的函数（FunctionTool对象）
```

#### Mock工具

```python
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

return mock_tool_func  # 返回装饰后的函数（FunctionTool对象）
```

## 参数类型注解

### 支持的类型

- `str`: 字符串类型
- `int`: 整数类型
- `float`: 浮点数类型
- `bool`: 布尔类型
- `List[T]`: 列表类型
- `Dict[str, T]`: 字典类型
- `Optional[T]`: 可选类型
- `**kwargs`: 可变关键字参数（用于动态参数）

### 示例

```python
from typing import List, Optional, Dict

@function_tool
async def complex_tool(
    name: str,
    age: int,
    score: float,
    is_active: bool,
    tags: List[str],
    metadata: Optional[Dict[str, str]] = None
) -> str:
    """
    复杂工具示例
    
    Args:
        name: 名称
        age: 年龄
        score: 分数
        is_active: 是否激活
        tags: 标签列表
        metadata: 元数据（可选）
        
    Returns:
        处理结果
    """
    return f"处理 {name}"
```

## 返回值

- 工具函数必须返回字符串（`str`）
- 如果需要返回复杂数据，可以将其序列化为 JSON 字符串

## 异步支持

- 工具函数可以是异步函数（`async def`）
- 异步函数可以调用其他异步服务（如数据库、API等）

## 在Agent中使用工具

```python
from agents import Agent

# 创建工具
rag_tool = _create_rag_tool(project_id, agent)

# 创建Agent并添加工具
agent = Agent(
    name="my_agent",
    instructions="你是一个助手...",
    tools=[rag_tool],  # 添加工具
)
```

## 注意事项

1. **函数必须返回字符串**：工具函数的返回值必须是字符串类型
2. **类型注解是必需的**：函数参数和返回值必须有类型注解
3. **文档字符串建议**：虽然可以使用 `description_override`，但建议在函数文档字符串中详细描述参数和返回值
4. **异步函数**：如果工具需要调用异步服务，使用 `async def` 定义函数
5. **错误处理**：工具函数应该处理可能的错误，并返回有意义的错误消息

## 完整示例

```python
from agents import function_tool
from typing import List, Optional
import json

@function_tool(
    name_override="search_documents",
    description_override="搜索相关文档"
)
async def search_documents(
    query: str,
    limit: int = 10,
    filters: Optional[List[str]] = None
) -> str:
    """
    搜索相关文档
    
    Args:
        query: 搜索查询
        limit: 返回结果数量限制
        filters: 过滤条件列表（可选）
        
    Returns:
        JSON格式的搜索结果
    """
    try:
        # 执行搜索逻辑
        results = await perform_search(query, limit, filters)
        
        # 转换为JSON字符串
        return json.dumps(results, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

# 使用工具
tool = search_documents  # 装饰后的函数已经是FunctionTool对象
```

## 参考

- OpenAI Agent SDK Python 官方文档：https://openai.github.io/openai-agents-python/
- 项目中的实现：`backend/app/services/agents/openai_agent_tools.py`

