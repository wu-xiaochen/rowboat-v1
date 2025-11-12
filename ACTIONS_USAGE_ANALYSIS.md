# Server Actions 使用情况分析
# Server Actions Usage Analysis

**创建日期**：2025-01-27  
**目的**：分析哪些Server Actions仍在被使用，哪些可以迁移到Python后端

## Actions使用情况统计

### 总览
- **Actions文件总数**：15个
- **仍在使用**：大部分仍在使用
- **已迁移到Python后端**：1个（playground-chat.actions.ts）

## 详细分析

### ✅ 已迁移到Python后端

1. **`playground-chat.actions.ts`** ✅
   - `createConversation` - 已标记`@deprecated`，不再使用
   - `createCachedTurn` - 已标记`@deprecated`，不再使用
   - **替代方案**：`chatApiClient` (src/application/lib/chat-api-client.ts)
   - **状态**：✅ 可以删除

### ⚠️ 仍在使用（需要保留）

1. **`project.actions.ts`** ⚠️
   - **使用位置**：46个文件
   - **主要功能**：项目管理（创建、更新、删除项目）
   - **状态**：⚠️ 仍在使用，但部分功能可能已迁移到Python后端
   - **建议**：检查哪些功能可以迁移

2. **`data-source.actions.ts`** ⚠️
   - **使用位置**：多个数据源相关组件
   - **主要功能**：数据源管理（创建、删除、更新）
   - **状态**：⚠️ 仍在使用
   - **建议**：需要实现Python后端API

3. **`custom-mcp-server.actions.ts`** ⚠️
   - **使用位置**：CustomMcpServer组件、ServerCard组件
   - **主要功能**：MCP服务器管理
   - **状态**：⚠️ 仍在使用
   - **建议**：需要实现Python后端API

4. **`conversation.actions.ts`** ⚠️
   - **使用位置**：对话列表、对话详情组件
   - **主要功能**：对话管理
   - **状态**：⚠️ 仍在使用
   - **建议**：需要实现Python后端API

5. **`copilot.actions.ts`** ⚠️
   - **使用位置**：Copilot相关组件
   - **主要功能**：Copilot功能
   - **状态**：⚠️ 仍在使用
   - **建议**：检查是否可以迁移到Python后端

6. **`composio.actions.ts`** ⚠️
   - **使用位置**：Composio工具相关组件
   - **主要功能**：Composio集成
   - **状态**：⚠️ 仍在使用
   - **建议**：检查是否可以迁移到Python后端

7. **`job.actions.ts`** ⚠️
   - **使用位置**：任务列表、任务详情组件
   - **主要功能**：任务管理
   - **状态**：⚠️ 仍在使用
   - **建议**：需要实现Python后端API

8. **`scheduled-job-rules.actions.ts`** ⚠️
   - **使用位置**：计划任务规则组件
   - **主要功能**：计划任务规则管理
   - **状态**：⚠️ 仍在使用
   - **建议**：需要实现Python后端API

9. **`recurring-job-rules.actions.ts`** ⚠️
   - **使用位置**：重复任务规则组件
   - **主要功能**：重复任务规则管理
   - **状态**：⚠️ 仍在使用
   - **建议**：需要实现Python后端API

10. **`assistant-templates.actions.ts`** ⚠️
    - **使用位置**：模板相关组件
    - **主要功能**：助手模板管理
    - **状态**：⚠️ 仍在使用
    - **建议**：检查是否可以迁移

11. **`shared-workflow.actions.ts`** ⚠️
    - **使用位置**：工作流相关组件
    - **主要功能**：工作流共享
    - **状态**：⚠️ 仍在使用
    - **建议**：检查是否可以迁移

12. **`auth.actions.ts`** ⚠️
    - **使用位置**：认证相关
    - **主要功能**：用户认证
    - **状态**：⚠️ 仍在使用
    - **建议**：可能不需要迁移（Next.js Server Actions适合处理认证）

13. **`billing.actions.ts`** ⚠️
    - **使用位置**：计费相关组件
    - **主要功能**：计费管理
    - **状态**：⚠️ 仍在使用
    - **建议**：可能不需要迁移

14. **`twilio.actions.ts`** ⚠️
    - **使用位置**：Twilio集成
    - **主要功能**：Twilio集成
    - **状态**：⚠️ 仍在使用（可选功能）
    - **建议**：可选功能，暂不迁移

## 迁移优先级

### 高优先级（核心功能）
1. **数据源管理** - 需要实现Python后端API
2. **对话管理** - 需要实现Python后端API
3. **任务管理** - 需要实现Python后端API

### 中优先级（重要功能）
1. **MCP服务器管理** - 需要实现Python后端API
2. **触发器管理** - 需要实现Python后端API
3. **Copilot功能** - 检查是否可以迁移

### 低优先级（可选功能）
1. **认证功能** - 可能不需要迁移
2. **计费功能** - 可能不需要迁移
3. **Twilio集成** - 可选功能

## 建议

### 立即操作
1. ✅ 删除或归档 `playground-chat.actions.ts`（已标记废弃）
2. ⚠️ 分析 `project.actions.ts` 的使用情况，确定哪些功能可以迁移
3. ⚠️ 实现数据源管理Python后端API

### 后续操作
1. 逐步实现其他功能的Python后端API
2. 迁移前端代码使用新的API
3. 删除已迁移的Server Actions

---

**维护者**：开发团队  
**最后更新**：2025-01-27

