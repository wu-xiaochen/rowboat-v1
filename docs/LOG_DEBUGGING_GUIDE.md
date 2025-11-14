# 日志调试指南

## 问题描述

用户报告：
1. Copilot 生成了流式输出
2. 到搜索工具的时候报错：`Error code: 400 - {'code': 20015, 'message': '"messages" in request are illegal: Message has tool role, but there was no previous assistant message with a tool call!..', 'data': None}`
3. 日志文件没有创建

## 分析

这个错误发生在**第二轮迭代**时（工具执行后继续生成响应），说明：
1. 第一轮迭代成功：LLM 返回了工具调用，工具执行成功
2. 第二轮迭代失败：在调用 LLM 时，消息顺序有问题

关键问题：在第二轮迭代开始时，`current_messages` 中可能已经包含了 `ToolMessage`，但之前的 `AIMessage` 可能没有正确包含 `tool_calls`。

## 已添加的调试功能

### 1. 日志文件输出
- 所有调试信息会同时输出到控制台和 `/tmp/backend_copilot.log`
- 日志文件在第一次调用 `_log_debug` 时创建

### 2. 详细的调试日志
- `🚀 Copilot stream_response 开始` - 函数开始
- `🔄 开始工具调用循环` - 循环开始
- `🔍 迭代 X 开始前，验证消息顺序` - 每轮迭代开始前的验证
- `📋 消息列表详情` - 消息列表的详细信息
- `✅ 手动构建AIMessage` - AIMessage 构建成功
- `🔧 ToolCall: name=..., id=...` - 工具调用的详细信息
- `📝 准备添加 ToolMessage` - 准备添加 ToolMessage
- `✅ 成功添加 ToolMessage` - ToolMessage 添加成功
- `🔍 迭代 X 完成后的消息列表状态` - 迭代完成后的状态
- `❌ 错误：...` - 任何错误信息

### 3. 错误检测和修复
- 在下一轮迭代开始前，验证消息顺序
- 如果发现问题，尝试修复或退出循环
- 捕获流式响应中的错误，并记录详细信息

## 如何查看日志

### 方法 1：实时查看（推荐）
```bash
tail -f /tmp/backend_copilot.log
```

### 方法 2：查看最近的日志
```bash
tail -n 100 /tmp/backend_copilot.log
```

### 方法 3：过滤关键信息
```bash
tail -f /tmp/backend_copilot.log | grep -E "迭代|AIMessage|ToolMessage|错误|警告|✅|❌"
```

## 关键检查点

### 检查点 1：第一轮迭代完成后
查看日志中是否有：
- `✅ 手动构建AIMessage，包含 N 个工具调用`
- `🔧 ToolCall: name=search_relevant_tools, id=...`
- `✅ 成功添加 M 个ToolMessage到消息列表`
- `🔍 迭代 1 完成后的消息列表状态`

**关键**：确认最后一条消息是 `ToolMessage`，前一条是包含 `tool_calls` 的 `AIMessage`。

### 检查点 2：第二轮迭代开始前
查看日志中是否有：
- `🔍 迭代 2 开始前，验证消息顺序`
- `✅ 消息顺序验证通过` 或 `❌ 错误：...`

**关键**：如果验证失败，会退出循环，避免错误。

### 检查点 3：第二轮迭代开始时
查看日志中是否有：
- `🚀 迭代 2 开始，调用 LLM，消息总数: X`
- `📋 消息列表详情（最后3条）`

**关键**：确认消息列表的顺序正确。

## 常见问题

### 问题 1：日志文件没有创建
**可能原因**：
- `_log_debug` 函数没有被调用
- 文件权限问题
- 路径问题

**解决方案**：
- 检查 `/tmp` 目录是否可写
- 检查后端服务是否有权限写入文件
- 查看控制台输出，确认是否有日志

### 问题 2：AIMessage 没有 tool_calls
**症状**：日志显示 `❌ 错误：最后一条AIMessage没有tool_calls`

**可能原因**：
- `final_ai_chunk` 不包含 `tool_calls`
- `all_tool_calls_collected` 为空
- `tool_calls_in_this_iteration` 为空

**解决方案**：
- 检查流式响应中是否正确收集了工具调用
- 检查工具调用解析逻辑

### 问题 3：tool_call_id 不匹配
**症状**：日志显示 `⚠️ 警告：发现不匹配的tool_call_id`

**可能原因**：
- `AIMessage` 中的 `tool_calls` 的 `id` 与 `ToolMessage` 的 `tool_call_id` 不一致

**解决方案**：
- 确保使用 `tool_calls_in_this_iteration` 构建 `AIMessage`
- 确保 `ToolMessage` 使用相同的 `tool_call_id`

## 下一步

1. **触发一个 Copilot 请求**（在前端输入"搜索相关工具"等）
2. **立即查看日志**：
   ```bash
   tail -f /tmp/backend_copilot.log
   ```
3. **根据日志信息定位问题**：
   - 如果看到 `❌ 错误：最后一条AIMessage没有tool_calls`，说明 AIMessage 构建失败
   - 如果看到 `❌ 错误：最后一条是 ToolMessage，但前一条 AIMessage 没有 tool_calls`，说明消息顺序错误
   - 如果看到 `❌ 流式响应错误`，说明在调用 LLM 时出错

## 相关文件

- `backend/app/services/copilot/copilot_service.py` - Copilot 服务实现
- `/tmp/backend_copilot.log` - 日志文件

