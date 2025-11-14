# 原项目与当前项目功能对比
# Original vs Current Project Feature Comparison

## 📋 功能清单对比

### ✅ 已实现功能

#### 后端API端点
- ✅ 健康检查 (`GET /api/v1/health`)
- ✅ Ping端点 (`GET /api/v1/ping`)
- ✅ API信息 (`GET /api/v1/info`)
- ✅ 项目管理
  - ✅ 创建项目 (`POST /api/v1/projects`)
  - ✅ 获取项目列表 (`GET /api/v1/projects`)
  - ✅ 获取项目详情 (`GET /api/v1/projects/{project_id}`)
  - ✅ 更新项目 (`PUT /api/v1/projects/{project_id}`)
  - ✅ 删除项目 (`DELETE /api/v1/projects/{project_id}`)
- ✅ API密钥管理
  - ✅ 创建API密钥 (`POST /api/v1/{project_id}/api-keys`)
  - ✅ 列出API密钥 (`GET /api/v1/{project_id}/api-keys`)
- ✅ 聊天功能
  - ✅ 流式聊天 (`POST /api/v1/{project_id}/chat`)
  - ✅ 非流式聊天 (`POST /api/v1/{project_id}/chat`)
- ✅ Copilot功能
  - ✅ Copilot流式响应 (`POST /api/v1/{project_id}/copilot/stream`)
  - ✅ 编辑智能体提示词 (`POST /api/v1/{project_id}/copilot/edit-agent-instructions`)

#### 前端功能
- ✅ 项目管理界面
- ✅ 工作流编辑器
- ✅ Playground聊天界面
- ✅ Copilot界面

---

### ❌ 遗漏功能（需要实现）

#### 1. 项目管理功能

##### 1.1 项目配置
- ❌ **旋转项目Secret** (`POST /api/v1/projects/{project_id}/rotate-secret`)
  - 原项目: `project.actions.ts::rotateSecret()`
  - 用途: 重新生成项目的secret，用于API认证
  - 优先级: 高

- ❌ **更新Webhook URL** (`PUT /api/v1/projects/{project_id}/webhook-url`)
  - 原项目: `project.actions.ts::updateWebhookUrl()`
  - 用途: 设置项目接收webhook的URL
  - 优先级: 中

- ❌ **更新项目名称** (`PUT /api/v1/projects/{project_id}/name`)
  - 原项目: `project.actions.ts::updateProjectName()`
  - 用途: 修改项目名称
  - 优先级: 高

##### 1.2 工作流管理
- ❌ **保存草稿工作流** (`PUT /api/v1/projects/{project_id}/draft-workflow`)
  - 原项目: `project.actions.ts::saveWorkflow()`
  - 用途: 保存工作流的草稿版本
  - 优先级: 高

- ❌ **发布工作流** (`PUT /api/v1/projects/{project_id}/live-workflow`)
  - 原项目: `project.actions.ts::publishWorkflow()`
  - 用途: 将草稿工作流发布为生产版本
  - 优先级: 高

- ❌ **回滚到生产工作流** (`POST /api/v1/projects/{project_id}/revert-to-live`)
  - 原项目: `project.actions.ts::revertToLiveWorkflow()`
  - 用途: 将草稿工作流回滚到生产版本
  - 优先级: 中

#### 2. 数据源（RAG）功能

##### 2.1 数据源管理
- ❌ **创建数据源** (`POST /api/v1/{project_id}/data-sources`)
  - 原项目: `data-source.actions.ts::createDataSource()`
  - 用途: 创建新的RAG数据源（文件、网页、文本等）
  - 优先级: 高

- ❌ **获取数据源列表** (`GET /api/v1/{project_id}/data-sources`)
  - 原项目: `data-source.actions.ts::listDataSources()`
  - 用途: 列出项目的所有数据源
  - 优先级: 高

- ❌ **获取数据源详情** (`GET /api/v1/{project_id}/data-sources/{source_id}`)
  - 原项目: `data-source.actions.ts::getDataSource()`
  - 用途: 获取单个数据源的详细信息
  - 优先级: 高

- ❌ **更新数据源** (`PUT /api/v1/{project_id}/data-sources/{source_id}`)
  - 原项目: `data-source.actions.ts::updateDataSource()`
  - 用途: 更新数据源配置
  - 优先级: 中

- ❌ **删除数据源** (`DELETE /api/v1/{project_id}/data-sources/{source_id}`)
  - 原项目: `data-source.actions.ts::deleteDataSource()`
  - 用途: 删除数据源
  - 优先级: 高

- ❌ **切换数据源状态** (`POST /api/v1/{project_id}/data-sources/{source_id}/toggle`)
  - 原项目: `data-source.actions.ts::toggleDataSource()`
  - 用途: 启用/禁用数据源
  - 优先级: 中

- ❌ **重新抓取网页数据源** (`POST /api/v1/{project_id}/data-sources/{source_id}/recrawl`)
  - 原项目: `data-source.actions.ts::recrawlWebDataSource()`
  - 用途: 重新抓取网页内容
  - 优先级: 低

##### 2.2 数据源文档管理
- ❌ **添加文档到数据源** (`POST /api/v1/{project_id}/data-sources/{source_id}/docs`)
  - 原项目: `data-source.actions.ts::addDocsToDataSource()`
  - 用途: 向数据源添加文档
  - 优先级: 高

- ❌ **列出数据源文档** (`GET /api/v1/{project_id}/data-sources/{source_id}/docs`)
  - 原项目: `data-source.actions.ts::listDocsInDataSource()`
  - 用途: 列出数据源中的所有文档
  - 优先级: 高

- ❌ **删除数据源文档** (`DELETE /api/v1/{project_id}/data-sources/{source_id}/docs/{doc_id}`)
  - 原项目: `data-source.actions.ts::deleteDocFromDataSource()`
  - 用途: 从数据源删除文档
  - 优先级: 中

##### 2.3 文件上传
- ❌ **获取文件上传URL** (`POST /api/v1/{project_id}/data-sources/{source_id}/upload-urls`)
  - 原项目: `data-source.actions.ts::getUploadUrlsForFilesDataSource()`
  - 用途: 获取文件上传的预签名URL（S3）
  - 优先级: 高

- ❌ **获取文件下载URL** (`GET /api/v1/{project_id}/data-sources/{source_id}/files/{file_id}/download-url`)
  - 原项目: `data-source.actions.ts::getDownloadUrlForFile()`
  - 用途: 获取文件下载的预签名URL
  - 优先级: 中

#### 3. 对话管理功能

##### 3.1 对话列表和详情
- ❌ **获取对话列表** (`GET /api/v1/{project_id}/conversations`)
  - 原项目: `conversation.actions.ts::listConversations()`
  - 用途: 列出项目的所有对话
  - 优先级: 高

- ❌ **获取对话详情** (`GET /api/v1/{project_id}/conversations/{conversation_id}`)
  - 原项目: `conversation.actions.ts::fetchConversation()`
  - 用途: 获取单个对话的详细信息
  - 优先级: 高

#### 4. 任务（Jobs）功能

##### 4.1 任务管理
- ❌ **获取任务列表** (`GET /api/v1/{project_id}/jobs`)
  - 原项目: `job.actions.ts::listJobs()`
  - 用途: 列出项目的所有任务（支持过滤、分页）
  - 优先级: 高

- ❌ **获取任务详情** (`GET /api/v1/{project_id}/jobs/{job_id}`)
  - 原项目: `job.actions.ts::fetchJob()`
  - 用途: 获取单个任务的详细信息
  - 优先级: 高

#### 5. Composio集成功能

##### 5.1 工具包（Toolkits）管理
- ❌ **列出工具包** (`GET /api/v1/{project_id}/composio/toolkits`)
  - 原项目: `composio.actions.ts::listToolkits()`
  - 用途: 列出可用的Composio工具包
  - 优先级: 中

- ❌ **获取工具包详情** (`GET /api/v1/{project_id}/composio/toolkits/{toolkit_slug}`)
  - 原项目: `composio.actions.ts::getToolkit()`
  - 用途: 获取工具包的详细信息
  - 优先级: 中

- ❌ **列出工具** (`GET /api/v1/{project_id}/composio/toolkits/{toolkit_slug}/tools`)
  - 原项目: `composio.actions.ts::listTools()`
  - 用途: 列出工具包中的所有工具
  - 优先级: 中

##### 5.2 连接账户（Connected Accounts）管理
- ❌ **创建OAuth2连接账户** (`POST /api/v1/{project_id}/composio/connected-accounts/oauth2`)
  - 原项目: `composio.actions.ts::createComposioManagedOauth2ConnectedAccount()`
  - 用途: 通过OAuth2创建Composio管理的连接账户
  - 优先级: 中

- ❌ **创建自定义连接账户** (`POST /api/v1/{project_id}/composio/connected-accounts/custom`)
  - 原项目: `composio.actions.ts::createCustomConnectedAccount()`
  - 用途: 创建自定义凭证的连接账户
  - 优先级: 低

- ❌ **同步连接账户** (`POST /api/v1/{project_id}/composio/connected-accounts/{account_id}/sync`)
  - 原项目: `composio.actions.ts::syncConnectedAccount()`
  - 用途: 同步连接账户的状态
  - 优先级: 低

- ❌ **删除连接账户** (`DELETE /api/v1/{project_id}/composio/connected-accounts/{account_id}`)
  - 原项目: `composio.actions.ts::deleteConnectedAccount()`
  - 用途: 删除连接账户
  - 优先级: 中

##### 5.3 触发器（Triggers）管理
- ❌ **列出触发器类型** (`GET /api/v1/{project_id}/composio/triggers/types`)
  - 原项目: `composio.actions.ts::listComposioTriggerTypes()`
  - 用途: 列出可用的触发器类型
  - 优先级: 低

- ❌ **创建触发器部署** (`POST /api/v1/{project_id}/composio/triggers/deployments`)
  - 原项目: `composio.actions.ts::createComposioTriggerDeployment()`
  - 用途: 创建新的触发器部署
  - 优先级: 低

- ❌ **列出触发器部署** (`GET /api/v1/{project_id}/composio/triggers/deployments`)
  - 原项目: `composio.actions.ts::listComposioTriggerDeployments()`
  - 用途: 列出项目的所有触发器部署
  - 优先级: 低

- ❌ **获取触发器部署详情** (`GET /api/v1/{project_id}/composio/triggers/deployments/{deployment_id}`)
  - 原项目: `composio.actions.ts::fetchComposioTriggerDeployment()`
  - 用途: 获取触发器部署的详细信息
  - 优先级: 低

- ❌ **删除触发器部署** (`DELETE /api/v1/{project_id}/composio/triggers/deployments/{deployment_id}`)
  - 原项目: `composio.actions.ts::deleteComposioTriggerDeployment()`
  - 用途: 删除触发器部署
  - 优先级: 低

##### 5.4 Composio Webhook
- ❌ **Composio Webhook接收** (`POST /api/composio/webhook`)
  - 原项目: `app/api/composio/webhook/route.ts`
  - 用途: 接收Composio的webhook事件
  - 优先级: 低

#### 6. 定时任务（Scheduled Jobs）功能

##### 6.1 定时任务规则
- ❌ **创建定时任务规则** (`POST /api/v1/{project_id}/scheduled-job-rules`)
  - 原项目: `scheduled-job-rules.actions.ts::createScheduledJobRule()`
  - 用途: 创建定时执行的任务规则
  - 优先级: 低

- ❌ **列出定时任务规则** (`GET /api/v1/{project_id}/scheduled-job-rules`)
  - 原项目: `scheduled-job-rules.actions.ts::listScheduledJobRules()`
  - 用途: 列出项目的所有定时任务规则
  - 优先级: 低

- ❌ **获取定时任务规则详情** (`GET /api/v1/{project_id}/scheduled-job-rules/{rule_id}`)
  - 原项目: `scheduled-job-rules.actions.ts::fetchScheduledJobRule()`
  - 用途: 获取定时任务规则的详细信息
  - 优先级: 低

- ❌ **删除定时任务规则** (`DELETE /api/v1/{project_id}/scheduled-job-rules/{rule_id}`)
  - 原项目: `scheduled-job-rules.actions.ts::deleteScheduledJobRule()`
  - 用途: 删除定时任务规则
  - 优先级: 低

#### 7. 循环任务（Recurring Jobs）功能

##### 7.1 循环任务规则
- ❌ **创建循环任务规则** (`POST /api/v1/{project_id}/recurring-job-rules`)
  - 原项目: `recurring-job-rules.actions.ts::createRecurringJobRule()`
  - 用途: 创建循环执行的任务规则
  - 优先级: 低

- ❌ **列出循环任务规则** (`GET /api/v1/{project_id}/recurring-job-rules`)
  - 原项目: `recurring-job-rules.actions.ts::listRecurringJobRules()`
  - 用途: 列出项目的所有循环任务规则
  - 优先级: 低

- ❌ **获取循环任务规则详情** (`GET /api/v1/{project_id}/recurring-job-rules/{rule_id}`)
  - 原项目: `recurring-job-rules.actions.ts::fetchRecurringJobRule()`
  - 用途: 获取循环任务规则的详细信息
  - 优先级: 低

- ❌ **切换循环任务规则状态** (`POST /api/v1/{project_id}/recurring-job-rules/{rule_id}/toggle`)
  - 原项目: `recurring-job-rules.actions.ts::toggleRecurringJobRule()`
  - 用途: 启用/禁用循环任务规则
  - 优先级: 低

- ❌ **删除循环任务规则** (`DELETE /api/v1/{project_id}/recurring-job-rules/{rule_id}`)
  - 原项目: `recurring-job-rules.actions.ts::deleteRecurringJobRule()`
  - 用途: 删除循环任务规则
  - 优先级: 低

#### 8. MCP服务器功能

##### 8.1 MCP服务器管理
- ❌ **添加MCP服务器** (`POST /api/v1/{project_id}/mcp-servers`)
  - 原项目: `custom-mcp-server.actions.ts::addServer()`
  - 用途: 添加自定义MCP服务器
  - 优先级: 中

- ❌ **删除MCP服务器** (`DELETE /api/v1/{project_id}/mcp-servers/{server_name}`)
  - 原项目: `custom-mcp-server.actions.ts::removeServer()`
  - 用途: 删除MCP服务器
  - 优先级: 中

- ❌ **获取MCP服务器工具** (`POST /api/v1/{project_id}/mcp-servers/{server_name}/fetch-tools`)
  - 原项目: `custom-mcp-server.actions.ts::fetchTools()`
  - 用途: 从MCP服务器获取可用工具列表
  - 优先级: 中

#### 9. 助手模板（Assistant Templates）功能

##### 9.1 模板管理
- ❌ **列出助手模板** (`GET /api/v1/assistant-templates`)
  - 原项目: `assistant-templates.actions.ts::listAssistantTemplates()`
  - 用途: 列出可用的助手模板
  - 优先级: 低

- ❌ **获取助手模板详情** (`GET /api/v1/assistant-templates/{template_id}`)
  - 原项目: `assistant-templates.actions.ts::getAssistantTemplate()`
  - 用途: 获取模板的详细信息
  - 优先级: 低

- ❌ **获取模板分类** (`GET /api/v1/assistant-templates/categories`)
  - 原项目: `assistant-templates.actions.ts::getAssistantTemplateCategories()`
  - 用途: 获取模板分类列表
  - 优先级: 低

- ❌ **创建助手模板** (`POST /api/v1/assistant-templates`)
  - 原项目: `assistant-templates.actions.ts::createAssistantTemplate()`
  - 用途: 创建新的助手模板
  - 优先级: 低

- ❌ **删除助手模板** (`DELETE /api/v1/assistant-templates/{template_id}`)
  - 原项目: `assistant-templates.actions.ts::deleteAssistantTemplate()`
  - 用途: 删除助手模板
  - 优先级: 低

- ❌ **切换模板点赞** (`POST /api/v1/assistant-templates/{template_id}/like`)
  - 原项目: `assistant-templates.actions.ts::toggleTemplateLike()`
  - 用途: 点赞/取消点赞模板
  - 优先级: 低

#### 10. 共享工作流功能

##### 10.1 工作流共享
- ❌ **创建共享工作流** (`POST /api/v1/shared-workflows`)
  - 原项目: `shared-workflow.actions.ts::createSharedWorkflowFromJson()`
  - 用途: 从JSON创建共享工作流（临时链接）
  - 优先级: 低

- ❌ **加载共享工作流** (`GET /api/v1/shared-workflows/{id}`)
  - 原项目: `shared-workflow.actions.ts::loadSharedWorkflow()`
  - 用途: 通过ID加载共享工作流
  - 优先级: 低

#### 11. Twilio语音功能

##### 11.1 Twilio配置
- ❌ **配置Twilio号码** (`POST /api/v1/{project_id}/twilio/configs`)
  - 原项目: `twilio.actions.ts::configureTwilioNumber()`
  - 用途: 配置Twilio电话号码用于语音通话
  - 优先级: 低

- ❌ **获取Twilio配置列表** (`GET /api/v1/{project_id}/twilio/configs`)
  - 原项目: `twilio.actions.ts::getTwilioConfigs()`
  - 用途: 列出项目的所有Twilio配置
  - 优先级: 低

- ❌ **删除Twilio配置** (`DELETE /api/v1/{project_id}/twilio/configs/{config_id}`)
  - 原项目: `twilio.actions.ts::deleteTwilioConfig()`
  - 用途: 删除Twilio配置
  - 优先级: 低

##### 11.2 Twilio Webhook
- ❌ **接收Twilio呼入** (`POST /api/twilio/inbound_call`)
  - 原项目: `app/api/twilio/inbound_call/route.ts`
  - 用途: 接收Twilio的呼入电话
  - 优先级: 低

- ❌ **处理Twilio对话轮次** (`POST /api/twilio/turn/{callSid}`)
  - 原项目: `app/api/twilio/turn/[callSid]/route.ts`
  - 用途: 处理Twilio通话中的对话轮次
  - 优先级: 低

#### 12. Widget功能（前端API）

##### 12.1 Widget会话管理
- ❌ **创建用户会话** (`POST /api/widget/v1/session/user`)
  - 原项目: `app/api/widget/v1/session/user/route.ts`
  - 用途: 为Widget创建用户会话
  - 优先级: 低

- ❌ **创建访客会话** (`POST /api/widget/v1/session/guest`)
  - 原项目: `app/api/widget/v1/session/guest/route.ts`
  - 用途: 为Widget创建访客会话
  - 优先级: 低

##### 12.2 Widget聊天管理
- ❌ **创建Widget聊天** (`POST /api/widget/v1/chats`)
  - 原项目: `app/api/widget/v1/chats/route.ts`
  - 用途: 创建Widget聊天会话
  - 优先级: 低

- ❌ **获取Widget聊天详情** (`GET /api/widget/v1/chats/{chatId}`)
  - 原项目: `app/api/widget/v1/chats/[chatId]/route.ts`
  - 用途: 获取Widget聊天详情
  - 优先级: 低

- ❌ **获取Widget聊天消息** (`GET /api/widget/v1/chats/{chatId}/messages`)
  - 原项目: `app/api/widget/v1/chats/[chatId]/messages/route.ts`
  - 用途: 获取Widget聊天的消息列表
  - 优先级: 低

- ❌ **处理Widget聊天轮次** (`POST /api/widget/v1/chats/{chatId}/turn`)
  - 原项目: `app/api/widget/v1/chats/[chatId]/turn/route.ts`
  - 用途: 处理Widget聊天的对话轮次
  - 优先级: 低

- ❌ **关闭Widget聊天** (`POST /api/widget/v1/chats/{chatId}/close`)
  - 原项目: `app/api/widget/v1/chats/[chatId]/close/route.ts`
  - 用途: 关闭Widget聊天会话
  - 优先级: 低

#### 13. 其他功能

##### 13.1 认证和用户
- ❌ **获取用户信息** (`GET /api/me`)
  - 原项目: `app/api/me/route.ts`
  - 用途: 获取当前登录用户信息
  - 优先级: 中

- ❌ **更新用户邮箱** (`PUT /api/auth/profile`)
  - 原项目: `app/api/auth/profile/route.ts`
  - 用途: 更新用户邮箱
  - 优先级: 低

##### 13.2 文件处理
- ❌ **获取临时图片** (`GET /api/tmp-images/{id}`)
  - 原项目: `app/api/tmp-images/[id]/route.ts`
  - 用途: 获取临时图片
  - 优先级: 低

- ❌ **获取生成的图片** (`GET /api/generated-images/{id}`)
  - 原项目: `app/api/generated-images/[id]/route.ts`
  - 用途: 获取生成的图片
  - 优先级: 低

##### 13.3 流式响应
- ❌ **获取流式响应** (`GET /api/stream-response/{streamId}`)
  - 原项目: `app/api/stream-response/[streamId]/route.ts`
  - 用途: 获取流式响应内容
  - 优先级: 低

- ❌ **获取Copilot流式响应** (`GET /api/copilot-stream-response/{streamId}`)
  - 原项目: `app/api/copilot-stream-response/[streamId]/route.ts`
  - 用途: 获取Copilot流式响应内容
  - 优先级: 低

##### 13.4 文件上传
- ❌ **文件上传处理** (`POST /api/uploads/{fileId}/...`)
  - 原项目: `app/api/uploads/[fileId]/...`
  - 用途: 处理文件上传
  - 优先级: 中

---

## 📊 功能统计

### 已实现功能
- **后端API端点**: 11个
- **前端页面**: 核心页面已实现

### 遗漏功能
- **后端API端点**: 约80+个
- **功能模块**: 13个主要模块

---

## 🎯 优先级建议

### 高优先级（核心功能）
1. **项目管理增强**
   - 旋转Secret
   - 更新项目名称
   - 保存/发布工作流
   - 回滚工作流

2. **数据源（RAG）管理**
   - 创建/列出/删除数据源
   - 添加/列出/删除文档
   - 文件上传/下载URL

3. **对话管理**
   - 列出对话
   - 获取对话详情

4. **任务管理**
   - 列出任务
   - 获取任务详情

### 中优先级（重要功能）
1. **MCP服务器管理**
2. **Composio工具包管理**
3. **用户信息管理**

### 低优先级（可选功能）
1. **定时任务和循环任务**
2. **Twilio语音功能**
3. **Widget功能**
4. **助手模板**
5. **共享工作流**
6. **Composio触发器**

---

## 📝 实现建议

### 阶段一：核心功能完善（高优先级）
1. 实现项目管理增强功能
2. 实现数据源管理功能
3. 实现对话和任务管理功能

### 阶段二：集成功能（中优先级）
1. 实现MCP服务器管理
2. 实现Composio基础功能
3. 完善用户认证

### 阶段三：扩展功能（低优先级）
1. 实现定时任务和循环任务
2. 实现Widget功能
3. 实现其他辅助功能

---

**最后更新**: 2025-01-27  
**状态**: 功能对比完成，待实现遗漏功能

