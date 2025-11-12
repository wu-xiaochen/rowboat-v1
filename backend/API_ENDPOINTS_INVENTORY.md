# API端点清单
# API Endpoints Inventory

本文档列举了原项目的所有API端点和Server Actions，用于对照检查，确保后端实现不遗漏任何功能。

This document lists all API endpoints and Server Actions from the original project for reference and comparison to ensure no functionality is missed in the backend implementation.

## 1. REST API端点 (REST API Endpoints)

### 1.1 核心API (Core API)
- **POST** `/api/v1/[projectId]/chat` - 聊天对话（主要API）
  - 功能：执行对话回合，获取智能体响应
  - 支持流式响应
  - 参数：conversationId, messages, mockTools, stream
  - 状态：✅ 已实现（步骤6.1-6.2）

### 1.2 流式响应 (Streaming Responses)
- **GET** `/api/copilot-stream-response/[streamId]` - Copilot流式响应
  - 功能：获取Copilot流式响应
  - 状态：⏳ 待实现（步骤6.2）
  
- **GET** `/api/stream-response/[streamId]` - 流式响应
  - 功能：获取对话流式响应
  - 状态：⏳ 待实现（步骤6.2）

### 1.3 图片和文件 (Images and Files)
- **GET** `/api/generated-images/[id]` - 生成的图片
  - 功能：获取生成的图片
  - 状态：⏳ 待实现
  
- **GET** `/api/tmp-images/[id]` - 临时图片
  - 功能：获取临时图片
  - 状态：⏳ 待实现
  
- **GET/POST** `/api/uploads/[fileId]` - 文件上传
  - 功能：上传和获取文件
  - 状态：⏳ 待实现

### 1.4 用户和认证 (User and Auth)
- **GET** `/api/me` - 当前用户信息
  - 功能：获取当前用户信息
  - 状态：⏳ 待实现（如果使用认证）

### 1.5 Webhooks
- **POST** `/api/composio/webhook` - Composio webhook
  - 功能：处理Composio webhook
  - 状态：⏳ 待实现

### 1.6 Twilio集成 (Twilio Integration) - 可选
- **POST** `/api/twilio/inbound_call` - Twilio入站呼叫
  - 功能：处理Twilio入站呼叫
  - 状态：❌ 暂未实现（原项目也未实现）

- **POST** `/api/twilio/turn/[callSid]` - Twilio回合
  - 功能：处理Twilio对话回合
  - 状态：❌ 暂未实现（原项目也未实现）

### 1.7 Widget API (Widget API) - 可选
- **POST** `/api/widget/v1/session/user` - 用户会话
  - 功能：创建用户会话
  - 状态：❌ 暂未实现（原项目也未实现）

- **POST** `/api/widget/v1/session/guest` - 访客会话
  - 功能：创建访客会话
  - 状态：⏳ 待实现（如果使用widget）

- **GET/POST** `/api/widget/v1/chats` - 聊天列表
  - 功能：获取和创建聊天
  - 状态：⏳ 待实现（如果使用widget）

- **GET** `/api/widget/v1/chats/[chatId]` - 聊天详情
  - 功能：获取聊天详情
  - 状态：⏳ 待实现（如果使用widget）

- **POST** `/api/widget/v1/chats/[chatId]/turn` - 聊天回合
  - 功能：执行聊天回合
  - 状态：⏳ 待实现（如果使用widget）

- **GET** `/api/widget/v1/chats/[chatId]/messages` - 聊天消息
  - 功能：获取聊天消息
  - 状态：⏳ 待实现（如果使用widget）

- **POST** `/api/widget/v1/chats/[chatId]/close` - 关闭聊天
  - 功能：关闭聊天
  - 状态：⏳ 待实现（如果使用widget）

## 2. Server Actions (Next.js Server Actions)

### 2.1 项目管理 (Project Management)
- `createProject` - 创建项目
  - 状态：✅ 已实现（步骤4.2）
  
- `createProjectFromWorkflowJson` - 从工作流JSON创建项目
  - 状态：⏳ 待实现
  
- `fetchProject` - 获取项目
  - 状态：✅ 已实现（步骤4.2）
  
- `listProjects` - 获取项目列表
  - 状态：✅ 已实现（步骤4.2）
  
- `updateProjectName` - 更新项目名称
  - 状态：✅ 已实现（步骤4.2）
  
- `updateWebhookUrl` - 更新Webhook URL
  - 状态：✅ 已实现（步骤4.2）
  
- `rotateSecret` - 旋转项目Secret
  - 状态：⏳ 待实现
  
- `updateDraftWorkflow` - 更新草稿工作流
  - 状态：✅ 已实现（步骤4.2）
  
- `updateLiveWorkflow` - 更新生产工作流
  - 状态：✅ 已实现（步骤4.2）
  
- `revertToLiveWorkflow` - 恢复到生产工作流
  - 状态：⏳ 待实现
  
- `deleteProject` - 删除项目
  - 状态：✅ 已实现（步骤4.2）

### 2.2 API密钥管理 (API Key Management)
- `createApiKey` - 创建API密钥
  - 状态：✅ 已实现（步骤4.1）
  
- `listApiKeys` - 获取API密钥列表
  - 状态：✅ 已实现（步骤4.1）
  
- `deleteApiKey` - 删除API密钥
  - 状态：✅ 已实现（步骤4.1）

### 2.3 Copilot功能 (Copilot Features)
- `getCopilotResponseStream` - 获取Copilot流式响应
  - 功能：获取Copilot流式响应
  - 状态：⏳ 待实现（步骤6.2）
  
- `getCopilotAgentInstructions` - 获取Copilot智能体提示词
  - 功能：获取编辑后的智能体提示词
  - 状态：⏳ 待实现（步骤5.1）

### 2.4 对话管理 (Conversation Management)
- `listConversations` - 获取对话列表
  - 状态：⏳ 待实现
  
- `fetchConversation` - 获取对话详情
  - 状态：⏳ 待实现
  
- `createConversation` - 创建对话（playground）
  - 状态：⏳ 待实现

### 2.5 数据源管理 (Data Source Management)
- `fetchDataSource` - 获取数据源
  - 状态：⏳ 待实现
  
- `listDataSources` - 获取数据源列表
  - 状态：⏳ 待实现
  
- `createDataSource` - 创建数据源
  - 状态：⏳ 待实现
  
- `updateDataSource` - 更新数据源
  - 状态：⏳ 待实现
  
- `deleteDataSource` - 删除数据源
  - 状态：⏳ 待实现
  
- `toggleDataSource` - 切换数据源状态
  - 状态：⏳ 待实现
  
- `recrawlWebDataSource` - 重新抓取Web数据源
  - 状态：⏳ 待实现
  
- `addDocsToDataSource` - 添加文档到数据源
  - 状态：⏳ 待实现
  
- `listDocsInDataSource` - 获取数据源中的文档列表
  - 状态：⏳ 待实现
  
- `deleteDocFromDataSource` - 从数据源删除文档
  - 状态：⏳ 待实现
  
- `getDownloadUrlForFile` - 获取文件下载URL
  - 状态：⏳ 待实现
  
- `getUploadUrlsForFiles` - 获取文件上传URL
  - 状态：⏳ 待实现

### 2.6 任务管理 (Job Management)
- `listJobs` - 获取任务列表
  - 状态：⏳ 待实现
  
- `fetchJob` - 获取任务详情
  - 状态：⏳ 待实现

### 2.7 定时任务规则 (Scheduled Job Rules)
- `createScheduledJobRule` - 创建定时任务规则
  - 状态：⏳ 待实现
  
- `listScheduledJobRules` - 获取定时任务规则列表
  - 状态：⏳ 待实现
  
- `fetchScheduledJobRule` - 获取定时任务规则详情
  - 状态：⏳ 待实现
  
- `toggleScheduledJobRule` - 切换定时任务规则状态
  - 状态：⏳ 待实现
  
- `deleteScheduledJobRule` - 删除定时任务规则
  - 状态：⏳ 待实现

### 2.8 循环任务规则 (Recurring Job Rules)
- `createRecurringJobRule` - 创建循环任务规则
  - 状态：⏳ 待实现
  
- `listRecurringJobRules` - 获取循环任务规则列表
  - 状态：⏳ 待实现
  
- `fetchRecurringJobRule` - 获取循环任务规则详情
  - 状态：⏳ 待实现
  
- `toggleRecurringJobRule` - 切换循环任务规则状态
  - 状态：⏳ 待实现
  
- `deleteRecurringJobRule` - 删除循环任务规则
  - 状态：⏳ 待实现

### 2.9 Composio集成 (Composio Integration)
- `listComposioConnectedAccounts` - 获取Composio连接账户列表
  - 状态：⏳ 待实现
  
- `createComposioConnectedAccount` - 创建Composio连接账户
  - 状态：⏳ 待实现
  
- `deleteComposioConnectedAccount` - 删除Composio连接账户
  - 状态：⏳ 待实现

### 2.10 自定义MCP服务器 (Custom MCP Servers)
- `addServer` - 添加MCP服务器
  - 状态：⏳ 待实现
  
- `removeServer` - 删除MCP服务器
  - 状态：⏳ 待实现
  
- `fetchTools` - 获取MCP服务器工具
  - 状态：⏳ 待实现

### 2.11 助手模板 (Assistant Templates)
- `listTemplates` - 获取模板列表
  - 状态：⏳ 待实现

### 2.12 认证 (Authentication)
- `authCheck` - 认证检查
  - 状态：⏳ 待实现（如果使用认证）

### 2.13 计费 (Billing) - 可选
- `getCustomer` - 获取客户信息
  - 状态：❌ 暂不实现（原项目可选）
  
- `authorizeUserAction` - 授权用户操作
  - 状态：❌ 暂不实现（原项目可选）

## 3. 已实现的端点 (Implemented Endpoints)

### 3.1 基础端点
- ✅ `GET /api/v1/health` - 健康检查
- ✅ `GET /api/v1/health/ping` - Ping检查
- ✅ `GET /api/v1/info` - 应用信息

### 3.2 项目管理
- ✅ `POST /api/v1/projects` - 创建项目
- ✅ `GET /api/v1/projects` - 获取项目列表
- ✅ `GET /api/v1/projects/{project_id}` - 获取项目详情
- ✅ `PUT /api/v1/projects/{project_id}` - 更新项目
- ✅ `DELETE /api/v1/projects/{project_id}` - 删除项目

### 3.3 API密钥管理
- ✅ `POST /api/v1/api-keys` - 创建API密钥
- ✅ `GET /api/v1/api-keys` - 获取API密钥列表
- ✅ `DELETE /api/v1/api-keys/{api_key_id}` - 删除API密钥

## 4. 待实现的端点 (Pending Endpoints)

### 4.1 核心功能（高优先级）
1. **聊天API** (步骤6.1-6.2)
   - `POST /api/v1/{project_id}/chat` - 聊天对话
   - `GET /api/v1/stream-response/{stream_id}` - 流式响应
   - `GET /api/v1/copilot-stream-response/{stream_id}` - Copilot流式响应

2. **Copilot API** (步骤5.1-5.2)
   - `POST /api/v1/{project_id}/copilot` - Copilot对话
   - `POST /api/v1/{project_id}/copilot/edit-agent` - 编辑智能体提示词

3. **对话管理** (步骤6.1)
   - `GET /api/v1/projects/{project_id}/conversations` - 获取对话列表
   - `GET /api/v1/conversations/{conversation_id}` - 获取对话详情
   - `POST /api/v1/projects/{project_id}/conversations` - 创建对话

### 4.2 数据源管理（中优先级）
4. **数据源API** (步骤5.3)
   - `GET /api/v1/projects/{project_id}/data-sources` - 获取数据源列表
   - `POST /api/v1/projects/{project_id}/data-sources` - 创建数据源
   - `GET /api/v1/data-sources/{data_source_id}` - 获取数据源详情
   - `PUT /api/v1/data-sources/{data_source_id}` - 更新数据源
   - `DELETE /api/v1/data-sources/{data_source_id}` - 删除数据源
   - `POST /api/v1/data-sources/{data_source_id}/recrawl` - 重新抓取
   - `POST /api/v1/data-sources/{data_source_id}/toggle` - 切换状态

### 4.3 任务管理（中优先级）
5. **任务API**
   - `GET /api/v1/projects/{project_id}/jobs` - 获取任务列表
   - `GET /api/v1/jobs/{job_id}` - 获取任务详情

### 4.4 可选功能（低优先级）
6. **文件上传**
   - `POST /api/v1/uploads` - 上传文件
   - `GET /api/v1/uploads/{file_id}` - 获取文件

7. **图片生成**
   - `GET /api/v1/generated-images/{id}` - 获取生成的图片
   - `GET /api/v1/tmp-images/{id}` - 获取临时图片

8. **Webhooks**
   - `POST /api/v1/webhooks/composio` - Composio webhook

9. **Widget API** (如果使用widget)
   - Widget相关端点

## 5. 实施优先级 (Implementation Priority)

### 高优先级 (High Priority)
1. ✅ 项目管理端点（步骤4.2）
2. ✅ API密钥管理（步骤4.1）
3. ⏳ 聊天API（步骤6.1-6.2）
4. ⏳ Copilot API（步骤5.1-5.2）
5. ⏳ 对话管理（步骤6.1）

### 中优先级 (Medium Priority)
6. ⏳ 数据源管理（步骤5.3）
7. ⏳ 任务管理
8. ⏳ 定时任务规则
9. ⏳ 循环任务规则

### 低优先级 (Low Priority)
10. ⏳ 文件上传
11. ⏳ 图片生成
12. ⏳ Webhooks
13. ⏳ Widget API
14. ❌ Twilio集成（原项目也未实现）
15. ❌ 计费功能（原项目可选）

## 6. 注意事项 (Notes)

1. **认证机制**：原项目使用Next.js Server Actions，前端直接调用。我们的后端需要提供RESTful API，前端通过HTTP调用。

2. **流式响应**：原项目使用Server-Sent Events (SSE)实现流式响应。我们的后端也需要实现SSE。

3. **Widget API**：原项目有Widget API，用于嵌入聊天窗口。如果需要此功能，需要实现相关端点。

4. **Twilio集成**：原项目的Twilio集成功能暂未实现，我们可以暂时不实现。

5. **计费功能**：原项目的计费功能是可选的，我们可以暂时不实现。

6. **数据源管理**：数据源管理是RAG功能的重要组成部分，需要实现。

7. **任务管理**：任务管理用于后台任务执行，需要实现。

## 7. 实施计划 (Implementation Plan)

### 阶段1：核心功能（已完成）
- ✅ 项目管理端点
- ✅ API密钥管理
- ✅ 基础框架

### 阶段2：Copilot功能（进行中）
- ✅ CopilotService基础实现（步骤5.1）
- ⏳ Copilot工具集成（步骤5.2）
- ⏳ RAG功能实现（步骤5.3）

### 阶段3：聊天功能（待实现）
- ⏳ 聊天API端点（步骤6.1）
- ⏳ 流式响应实现（步骤6.2）

### 阶段4：数据源管理（待实现）
- ⏳ 数据源API端点
- ⏳ 数据源Repository
- ⏳ 数据源服务

### 阶段5：任务管理（待实现）
- ⏳ 任务API端点
- ⏳ 任务Repository
- ⏳ 任务服务

### 阶段6：可选功能（待实现）
- ⏳ 文件上传
- ⏳ 图片生成
- ⏳ Webhooks
- ⏳ Widget API

---

**最后更新**：2025-01-27  
**维护者**：开发团队

