# Copilot 工具调用实现 - 复刻原项目

## 实现说明

基于原项目的 `streamText` 实现，使用 LangChain Python API 重新实现了完整的工具调用处理逻辑。

## 原项目实现（TypeScript）

原项目使用 `ai` SDK 的 `streamText`：
- `maxSteps: 10` - 最多10轮工具调用迭代
- 自动处理多轮工具调用
- 事件类型：`text-delta`, `tool-call`, `tool-result`, `step-finish`

## Python 后端实现

### 核心逻辑

1. **多轮迭代循环**：
   - 最多执行 10 轮迭代（对应原项目的 `maxSteps: 10`）
   - 每轮迭代：LLM 响应 → 工具调用 → 工具执行 → 继续下一轮

2. **消息历史管理**：
   - `current_messages` 维护完整的消息历史
   - 每轮迭代添加 `AIMessage`（包含 `tool_calls`）和 `ToolMessage`

3. **工具调用处理**：
   - 收集流式响应中的工具调用
   - 使用 `ToolCall` 对象构建 `AIMessage`
   - 执行工具并创建 `ToolMessage`
   - 确保消息顺序：`AIMessage`（含 `tool_calls`）→ `ToolMessage`

### 关键修复

1. **安全获取 tool_call id**：
   ```python
   def _get_tool_call_id(tc):
       """安全获取 tool_call 的 id，支持字典和对象格式"""
       if isinstance(tc, dict):
           return tc.get('id', '')
       else:
           return getattr(tc, 'id', None) or ''
   ```

2. **正确处理 ToolCall**：
   - `ToolCall` 是 TypedDict，不能使用 `isinstance()` 检查
   - 使用 `_get_tool_call_id()` 安全获取 id
   - 使用 `ToolCall` 对象构建 `AIMessage`

3. **消息顺序保证**：
   - 先添加 `AIMessage`（包含 `tool_calls`）
   - 再添加 `ToolMessage`
   - 确保 OpenAI API 兼容性

## 与原项目的对应关系

| 原项目（TypeScript） | Python 后端 |
|---------------------|------------|
| `streamText({ maxSteps: 10 })` | `while iteration < 10` 循环 |
| `event.type === "text-delta"` | `yield CopilotStreamEvent(content=...)` |
| `event.type === "tool-call"` | `yield CopilotStreamEvent(type="tool-call", ...)` |
| `event.type === "tool-result"` | `yield CopilotStreamEvent(type="tool-result", ...)` |
| 自动消息管理 | 手动管理 `current_messages` |

## 测试要点

1. **工具调用流程**：
   - 第一轮：LLM 返回工具调用 → 执行工具 → 添加 ToolMessage
   - 第二轮：LLM 基于工具结果继续生成 → 可能再次调用工具
   - 最多 10 轮迭代

2. **消息顺序验证**：
   - 确保 `AIMessage`（含 `tool_calls`）在 `ToolMessage` 之前
   - 确保 `tool_call_id` 匹配

3. **错误处理**：
   - 工具调用错误不应中断整个流程
   - 流式响应错误应正确捕获和报告

## 注意事项

1. **ToolCall 是 TypedDict**：
   - 不能使用 `isinstance(tc, ToolCall)` 检查
   - 使用 `_get_tool_call_id()` 安全访问属性

2. **消息顺序**：
   - OpenAI API 要求：`AIMessage`（含 `tool_calls`）必须在 `ToolMessage` 之前
   - 违反此顺序会导致 `Error code: 20015`

3. **流式响应**：
   - LangChain 的流式响应可能分散在多个 chunk 中
   - 需要收集所有 chunk 以构建完整的 `AIMessage`

