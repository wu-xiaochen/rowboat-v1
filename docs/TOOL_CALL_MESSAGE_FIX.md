# 工具调用消息格式修复

## 问题描述

在Copilot流式响应中，遇到以下错误：
```
Error code: 400 - {'code': 20015, 'message': '"messages" in request are illegal: Message has tool role, but there was no previous assistant message with a tool call!..', 'data': None}
```

## 问题原因

OpenAI API要求：如果消息列表中有工具消息（ToolMessage），则必须在此之前有一个包含工具调用的助手消息（AIMessage with tool_calls）。

之前的实现中：
1. 在流式响应中收集工具调用
2. 执行工具调用，创建ToolMessage
3. 将ToolMessage添加到消息列表
4. **但是缺少了包含工具调用的AIMessage**

## 解决方案

### 1. 修复消息构建逻辑

在流式响应完成后：
1. **先构建包含工具调用的AIMessage**：使用LangChain的`ToolCall`对象
2. **将AIMessage添加到消息列表**
3. **然后执行工具调用，创建ToolMessage**
4. **最后将ToolMessage添加到消息列表**

### 2. 使用正确的ToolCall格式

LangChain的`AIMessage`需要`ToolCall`对象列表，而不是字典列表：

```python
from langchain_core.messages.tool import ToolCall

# 创建ToolCall对象
formatted_tool_calls = []
for tool_call_info in tool_calls_in_this_iteration:
    formatted_tool_calls.append(
        ToolCall(
            name=tool_name,
            args=tool_args,
            id=tool_call_id,
        )
    )

# 创建包含工具调用的AIMessage
ai_message_with_tools = AIMessage(
    content=assistant_message_content or "",
    tool_calls=formatted_tool_calls
)
current_messages.append(ai_message_with_tools)
```

### 3. 确保消息顺序

正确的消息顺序应该是：
1. SystemMessage
2. HumanMessage(s)
3. **AIMessage (with tool_calls)** ← 新增
4. ToolMessage(s) ← 对应上面的tool_calls
5. AIMessage (final response)

## 修改文件

- `backend/app/services/copilot/copilot_service.py`
  - 导入`ToolCall`从`langchain_core.messages.tool`
  - 在流式响应完成后，先构建包含工具调用的`AIMessage`
  - 使用`ToolCall`对象而不是字典来创建工具调用

## 验证

修复后，Copilot流式响应应该能够：
1. 正确构建包含工具调用的AIMessage
2. 在添加ToolMessage之前，先添加AIMessage
3. 满足OpenAI API的消息格式要求

## 相关文档

- [OpenAI API Tool Calling](https://platform.openai.com/docs/guides/function-calling)
- [LangChain ToolCall Documentation](https://python.langchain.com/docs/modules/messages/tool_calls/)

