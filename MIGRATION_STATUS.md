# 后端迁移状态 (Backend Migration Status)

## 概述 (Overview)

本项目已完成从旧的前端 Agents Runtime 到新的 Python 后端的迁移。本文档记录了迁移状态和已弃用的代码位置。

This project has completed migration from the old frontend Agents Runtime to the new Python backend. This document records the migration status and deprecated code locations.

## ✅ 已迁移的功能 (Migrated Features)

### 1. Copilot 功能
- **状态**: ✅ 已完全迁移
- **新后端端点**: `POST /api/v1/{project_id}/copilot/stream`
- **前端实现**: `apps/rowboat/app/projects/[projectId]/copilot/use-copilot.tsx`
- **后端实现**: `backend/app/services/copilot/copilot_service.py`
- **前端代理**: `apps/rowboat/app/api/v1/[projectId]/copilot/stream/route.ts`

### 2. 聊天功能 (Chat)
- **状态**: ✅ 已完全迁移
- **新后端端点**: `POST /api/v1/{project_id}/chat`
- **前端实现**: `apps/rowboat/app/projects/[projectId]/playground/components/chat.tsx`
- **后端实现**: `backend/app/services/chat/chat_service.py`
- **前端代理**: `apps/rowboat/app/api/v1/[projectId]/chat/route.ts`

### 3. Agents Runtime
- **状态**: ✅ 已完全迁移
- **新后端端点**: `POST /api/v1/{project_id}/chat` (使用 Agents Service)
- **后端实现**: `backend/app/services/agents/agents_service.py`
- **框架**: OpenAI Agent SDK Python

## ⚠️ 已弃用的代码 (Deprecated Code)

以下代码已标记为已弃用，但保留用于向后兼容和调试参考：

The following code has been marked as deprecated but is kept for backward compatibility and debugging reference:

### 1. 旧的 Agents Runtime
- **位置**: `apps/rowboat/src/application/lib/agents-runtime/`
- **状态**: ⚠️ 已弃用，但保留
- **说明**: 包含旧的 TypeScript Agents Runtime 实现，已迁移到 Python 后端
- **何时删除**: 确认所有功能都通过后端后，可以删除

### 2. 旧的 Use Case
- **位置**: `apps/rowboat/src/application/use-cases/conversations/run-conversation-turn.use-case.ts`
- **状态**: ⚠️ 已弃用，但可能仍被某些内部代码使用
- **说明**: 使用旧的 `streamResponse` 函数，新的请求应该通过后端 API
- **何时删除**: 确认所有调用都通过后端后，可以删除

### 3. 旧的 API 路由（已禁用）
以下路由已返回 501 Not Implemented，因为它们应该通过后端 API：

The following routes return 501 Not Implemented as they should go through backend API:

- `apps/rowboat/app/api/widget/v1/chats/[chatId]/turn/route.ts`
- `apps/rowboat/app/api/twilio/turn/[callSid]/route.ts`
- `apps/rowboat/app/api/twilio/inbound_call/route.ts`

## 📋 迁移检查清单 (Migration Checklist)

### 前端代码
- [x] Copilot 功能迁移到后端
- [x] 聊天功能迁移到后端
- [x] 前端 API 路由改为代理到后端
- [x] 修复所有 `PROVIDER_*` 环境变量引用
- [x] 标记旧的 agents-runtime 为已弃用

### 后端代码
- [x] Copilot 服务实现（LangChain）
- [x] Chat 服务实现（OpenAI Agent SDK）
- [x] Agents 服务实现（OpenAI Agent SDK）
- [x] API 端点实现
- [x] 配置管理统一

### 待处理 (Pending)
- [ ] 确认所有内部代码不再使用旧的 `streamResponse`
- [ ] 删除旧的 agents-runtime 代码（如果不再需要）
- [ ] 删除旧的 use case（如果不再需要）
- [ ] 更新文档和注释

## 🔍 如何识别旧代码 (How to Identify Old Code)

### 搜索模式
以下模式可以帮助识别仍在使用旧实现的代码：

The following patterns can help identify code still using old implementation:

```bash
# 搜索旧的 agents runtime 使用
grep -r "streamResponse" apps/rowboat/
grep -r "from.*agents-runtime" apps/rowboat/
grep -r "getResponse" apps/rowboat/

# 搜索旧的 PROVIDER_* 环境变量
grep -r "PROVIDER_API_KEY\|PROVIDER_BASE_URL" apps/rowboat/
```

### 已弃用标记
已弃用的代码文件包含以下标记：

Deprecated code files contain the following markers:

```typescript
/**
 * ⚠️ 已弃用：...
 * ⚠️ DEPRECATED: ...
 */
```

## 🚀 新代码应该使用 (New Code Should Use)

### API 端点
- **聊天**: `POST /api/v1/{project_id}/chat`
- **Copilot**: `POST /api/v1/{project_id}/copilot/stream`
- **编辑智能体提示词**: `POST /api/v1/{project_id}/copilot/edit-agent-instructions`

### 前端客户端
- **聊天客户端**: `apps/rowboat/src/application/lib/chat-api-client.ts`
- **Copilot Hook**: `apps/rowboat/app/projects/[projectId]/copilot/use-copilot.tsx`

### 环境变量
- **LLM配置**: `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL_ID`
- **Embedding配置**: `EMBEDDING_API_KEY`, `EMBEDDING_BASE_URL`, `EMBEDDING_MODEL`
- **后端地址**: `NEXT_PUBLIC_API_BASE_URL` (默认: `http://localhost:8001`)

## 📝 注意事项 (Notes)

1. **不要删除已弃用的代码**，除非确认所有功能都通过后端
2. **新功能必须使用后端 API**，不要直接调用旧的 agents runtime
3. **调试时可以参考旧代码**，但不要在新代码中使用
4. **环境变量已统一**，不再使用 `PROVIDER_*` 前缀

## 🔗 相关文档 (Related Documentation)

- 项目规则: `PROJECT-RULES.md`
- 开发计划: `DEVELOPMENT-PLAN.md`
- 后端 README: `backend/README.md`

---

**最后更新**: 2025-01-27  
**维护者**: 开发团队

