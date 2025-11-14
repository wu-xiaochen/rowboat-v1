# 工具调用消息顺序修复 V2

## 问题描述

错误信息：
```
Error code: 400 - {'code': 20015, 'message': '"messages" in request are illegal: Message has tool role, but there was no previous assistant message with a tool call!..', 'data': None}
```

这个错误表明在发送 `ToolMessage` 之前，没有先发送包含 `tool_calls` 的 `AIMessage`。

## 原项目 vs 当前实现对比

### 原项目（TypeScript）
- 使用 `@ai-sdk/openai` 的 `streamText` 函数
- **自动管理消息顺序**，包括工具调用和工具结果
- 不需要手动构建 `AIMessage` 和 `ToolMessage`，SDK 自动处理

### 当前实现（Python/LangChain）
- 使用 LangChain 的 `llm_with_tools.astream()`
- **需要手动管理消息顺序**
- 问题：在流式响应完成后，可能还没有收集到完整的 `AIMessage`（包含 `tool_calls`），就直接添加了 `ToolMessage`

## 修复方案

### 1. 优先使用 `tool_calls_in_this_iteration` 构建 `AIMessage`

**原因**：
- `tool_calls_in_this_iteration` 是我们在流式响应过程中收集的所有工具调用
- `tool_call_id` 是我们在 yield `tool-call` 事件时使用的，必须与 `ToolMessage` 中的 `tool_call_id` 匹配

**修改**：
```python
# 关键：优先使用 tool_calls_in_this_iteration，因为这是我们在流式响应过程中收集的所有工具调用
# 并且 tool_call_id 是我们在 yield tool-call 事件时使用的，必须与 ToolMessage 中的 tool_call_id 匹配
if tool_calls_in_this_iteration:
    for tool_call_info in tool_calls_in_this_iteration:
        tool_call_id = tool_call_info.get('id') or f"call_{uuid.uuid4().hex[:8]}"
        tool_name = tool_call_info.get('name', '').strip() if tool_call_info.get('name') else ''
        tool_args = tool_call_info.get('args', {})
        
        if not tool_name:
            continue
        
        # 创建ToolCall对象（LangChain格式）
        # 关键：使用与 yield tool-call 事件时相同的 tool_call_id
        formatted_tool_calls.append(
            ToolCall(
                name=tool_name,
                args=tool_args,
                id=tool_call_id,  # 必须与 ToolMessage 中的 tool_call_id 匹配
            )
        )
```

### 2. 添加严格的验证和修复逻辑

**验证**：
- 在添加 `ToolMessage` 之前，验证最后一条消息是 `AIMessage` 且包含 `tool_calls`
- 验证每个 `ToolMessage` 的 `tool_call_id` 是否在 `AIMessage` 的 `tool_calls` 中

**修复**：
- 如果 `AIMessage` 存在但没有 `tool_calls`，重新构建包含 `tool_calls` 的 `AIMessage`
- 如果最后一条消息不是 `AIMessage`，添加一个包含 `tool_calls` 的 `AIMessage`

**代码**：
```python
if current_messages and isinstance(current_messages[-1], AIMessage):
    last_ai_message = current_messages[-1]
    # 验证最后一条AIMessage是否包含tool_calls
    if hasattr(last_ai_message, 'tool_calls') and last_ai_message.tool_calls:
        # 验证每个ToolMessage的tool_call_id是否在AIMessage的tool_calls中
        ai_tool_call_ids = {tc.id for tc in last_ai_message.tool_calls}
        tool_message_ids = {tm.tool_call_id for tm in tool_messages}
        
        # 检查是否有不匹配的tool_call_id
        unmatched_ids = tool_message_ids - ai_tool_call_ids
        if unmatched_ids:
            print(f"⚠️ 警告：发现不匹配的tool_call_id: {unmatched_ids}")
        
        # 最后一条是AIMessage且包含tool_calls，可以安全添加ToolMessage
        current_messages.extend(tool_messages)
    else:
        # AIMessage存在但没有tool_calls，尝试修复
        if tool_calls_in_this_iteration:
            # 重新构建包含tool_calls的AIMessage
            # ... 修复逻辑 ...
```

### 3. 添加调试日志

添加详细的调试日志，帮助诊断问题：
- 打印所有工具调用的 ID，确保与 `ToolMessage` 匹配
- 打印消息列表的状态
- 打印验证结果

## 测试

1. 重启后端服务
2. 运行 Playwright 测试
3. 检查后端日志，确认：
   - `AIMessage` 正确构建，包含所有工具调用
   - `tool_call_id` 匹配
   - `ToolMessage` 正确添加

## 预期结果

- 不再出现 `Message has tool role, but there was no previous assistant message with a tool call!` 错误
- 工具调用正常工作
- 流式响应正常

## 相关文件

- `backend/app/services/copilot/copilot_service.py` - Copilot 服务实现

