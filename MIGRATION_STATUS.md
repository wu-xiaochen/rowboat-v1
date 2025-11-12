# 前后端迁移状态
# Frontend-Backend Migration Status

**创建日期**：2025-01-27  
**目的**：跟踪哪些功能已从Next.js Server Actions迁移到Python后端

## 迁移状态总览

### ✅ 已迁移到Python后端

1. **聊天功能（Chat）** ✅
   - **原实现**：`app/actions/playground-chat.actions.ts` 中的 `createConversation` 和 `createCachedTurn`
   - **新实现**：`backend/app/api/v1/endpoints/chat.py` - `POST /api/v1/{project_id}/chat`
   - **前端使用**：`apps/rowboat/app/projects/[projectId]/playground/components/chat.tsx` 使用 `chatApiClient`
   - **状态**：✅ 完全迁移，原actions不再使用

2. **项目管理** ⚠️
   - **原实现**：`app/actions/project.actions.ts`
   - **新实现**：`backend/app/api/v1/endpoints/projects.py`
   - **状态**：⚠️ 部分迁移，需要检查哪些功能还在使用原actions

3. **对话管理** ⚠️
   - **原实现**：`app/actions/conversation.actions.ts`
   - **新实现**：`backend/app/api/v1/endpoints/conversations.py`（如果已实现）
   - **状态**：⚠️ 需要检查

### ⚠️ 待迁移或部分迁移

1. **数据源管理**
   - **原实现**：`app/actions/data-source.actions.ts`
   - **新实现**：待实现
   - **状态**：⚠️ 仍在使用原actions

2. **Copilot功能**
   - **原实现**：`app/actions/copilot.actions.ts`
   - **新实现**：`backend/app/services/copilot/copilot_service.py`
   - **状态**：⚠️ 需要检查前端是否已迁移

3. **Composio集成**
   - **原实现**：`app/actions/composio.actions.ts`
   - **新实现**：`backend/app/services/composio/composio_service.py`
   - **状态**：⚠️ 需要检查前端是否已迁移

4. **任务管理**
   - **原实现**：`app/actions/job.actions.ts`
   - **新实现**：待实现
   - **状态**：⚠️ 仍在使用原actions

5. **触发器管理**
   - **原实现**：`app/actions/scheduled-job-rules.actions.ts`, `app/actions/recurring-job-rules.actions.ts`
   - **新实现**：待实现
   - **状态**：⚠️ 仍在使用原actions

### ❌ 未迁移（可能不需要）

1. **认证功能**
   - **原实现**：`app/actions/auth.actions.ts`
   - **状态**：❌ 可能不需要迁移（Next.js Server Actions适合处理认证）

2. **计费功能**
   - **原实现**：`app/actions/billing.actions.ts`
   - **状态**：❌ 可能不需要迁移

3. **Twilio集成**
   - **原实现**：`app/actions/twilio.actions.ts`
   - **状态**：❌ 可选功能，暂不迁移

## 可删除的原后端代码

### 已确认不再使用

1. **`app/actions/playground-chat.actions.ts`** ✅
   - `createConversation` - 不再使用（已迁移到Python后端）
   - `createCachedTurn` - 不再使用（已迁移到Python后端）
   - **建议**：可以删除或标记为废弃

### 需要进一步检查

1. **`app/api/v1/[projectId]/chat/route.ts`** ⚠️
   - 如果已完全迁移到Python后端，可以删除
   - 需要确认前端不再使用此路由

## 迁移建议

### 立即操作
1. ✅ 删除或标记废弃 `playground-chat.actions.ts` 中的已迁移函数
2. ⚠️ 检查并标记其他actions的迁移状态
3. ⚠️ 创建API端点清单，确保所有功能都有对应的Python后端实现

### 后续迁移
1. 数据源管理API
2. 任务管理API
3. 触发器管理API
4. Copilot API端点（如果前端需要）

---

**维护者**：开发团队  
**最后更新**：2025-01-27

