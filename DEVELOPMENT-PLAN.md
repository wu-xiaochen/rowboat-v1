# 详细开发计划 (Detailed Development Plan)

## 项目目标回顾
- 前后端完全分离
- 前端：保留所有功能，中文本地化，品牌替换（rowboat → 质信智购）
- 后端：Python + FastAPI + LangChain + CrewAI
- 所有配置外部化，禁止硬编码
- 高度解耦设计，新功能不影响旧功能
- 每步完成后测试和审视

## 开发阶段划分

### 阶段一：项目初始化和基础架构 (Phase 1: Project Initialization)

#### 步骤 1.1: Git仓库初始化和GitHub连接
- [ ] 初始化Git仓库（如未初始化）
- [ ] 创建.gitignore文件（包含Python、Node.js、环境变量等）
- [ ] 连接GitHub远程仓库：https://github.com/wu-xiaochen/rowboat-v1
- [ ] 创建初始提交
- [ ] 推送到GitHub
- **验收标准**：代码已推送到GitHub，.gitignore正确配置

#### 步骤 1.2: 后端项目结构初始化
- [ ] 创建backend目录结构
- [ ] 创建requirements.txt（包含FastAPI、LangChain、CrewAI等）
- [ ] 创建.env.example模板文件
- [ ] 创建app/core/config.py（使用pydantic-settings）
- [ ] 创建main.py入口文件
- [ ] 创建基础测试目录结构
- **验收标准**：目录结构符合规范，配置文件可加载，无硬编码

#### 步骤 1.3: 配置管理系统实现
- [ ] 实现Settings类（app/core/config.py）
- [ ] 配置所有必需的环境变量
- [ ] 实现配置验证逻辑
- [ ] 编写配置加载测试
- [ ] 提交代码并推送到GitHub
- **验收标准**：配置可正确加载，启动时验证通过，测试通过

#### 步骤 1.4: 数据库连接实现
- [ ] 实现MongoDB连接（app/core/database.py）
- [ ] 实现Redis连接（如需要）
- [ ] 实现Qdrant连接（如需要）
- [ ] 编写数据库连接测试
- [ ] 提交代码并推送到GitHub
- **验收标准**：所有数据库连接正常，测试通过

### 阶段二：核心数据层实现 (Phase 2: Core Data Layer)

#### 步骤 2.1: 数据模型定义
- [ ] 创建Pydantic模型（app/models/schemas.py）
- [ ] 定义Project模型
- [ ] 定义Conversation模型
- [ ] 定义Agent模型
- [ ] 定义Message模型
- [ ] 编写模型验证测试
- **验收标准**：所有模型定义完整，验证逻辑正确

#### 步骤 2.2: Repository层实现
- [ ] 创建ProjectsRepository（app/repositories/projects.py）
- [ ] 实现CRUD操作
- [ ] 创建ConversationsRepository
- [ ] 创建AgentsRepository
- [ ] 编写Repository测试
- [ ] 提交代码并推送到GitHub
- **验收标准**：Repository操作正常，测试覆盖率>70%

### 阶段三：FastAPI基础框架 (Phase 3: FastAPI Foundation)

#### 步骤 3.1: FastAPI应用初始化
- [ ] 创建FastAPI应用实例
- [ ] 配置CORS
- [ ] 配置OpenAPI文档
- [ ] 实现统一响应格式
- [ ] 实现错误处理中间件
- [ ] 编写基础API测试
- **验收标准**：FastAPI应用可启动，CORS配置正确，文档可访问

#### 步骤 3.2: 基础API端点实现
- [ ] 实现健康检查端点：GET /health
- [ ] 实现API信息端点：GET /api/v1/info
- [ ] 编写端点测试
- [ ] 提交代码并推送到GitHub
- **验收标准**：端点响应正确，测试通过

### 阶段四：项目管理API (Phase 4: Project Management API)

#### 步骤 4.1: 项目管理端点
- [ ] 实现GET /api/v1/projects（列表）
- [ ] 实现POST /api/v1/projects（创建）
- [ ] 实现GET /api/v1/projects/{project_id}（详情）
- [ ] 实现PUT /api/v1/projects/{project_id}（更新）
- [ ] 实现DELETE /api/v1/projects/{project_id}（删除）
- [ ] 编写完整测试
- [ ] 提交代码并推送到GitHub
- **验收标准**：所有端点功能正常，测试通过，符合RESTful规范

### 阶段五：LangChain Copilot服务 (Phase 5: LangChain Copilot Service)

#### 步骤 5.1: LangChain基础集成
- [ ] 创建CopilotService类（app/services/copilot/copilot_service.py）
- [ ] 实现LLM初始化（使用配置的provider）
- [ ] 实现基础对话功能
- [ ] 编写服务测试
- [ ] 提交代码并推送到GitHub
- **验收标准**：LangChain集成正常，可进行基础对话

#### 步骤 5.2: Copilot工具集成
- [ ] 实现工具加载机制
- [ ] 实现工具调用逻辑
- [ ] 支持Composio工具集成
- [ ] 编写工具测试
- [ ] 提交代码并推送到GitHub
- **验收标准**：工具可正常调用，测试通过

#### 步骤 5.3: RAG功能实现
- [ ] 实现向量存储（Qdrant）
- [ ] 实现文档嵌入（使用配置的embedding模型）
- [ ] 实现检索逻辑
- [ ] 集成到Copilot服务
- [ ] 编写RAG测试
- [ ] 提交代码并推送到GitHub
- **验收标准**：RAG功能正常，检索准确

### 阶段六：聊天API实现 (Phase 6: Chat API Implementation)

#### 步骤 6.1: 聊天端点基础
- [ ] 实现POST /api/v1/{project_id}/chat
- [ ] 实现消息存储
- [ ] 实现对话历史管理
- [ ] 编写基础测试
- [ ] 提交代码并推送到GitHub
- **验收标准**：聊天端点可正常调用，消息可存储

#### 步骤 6.2: 流式响应实现
- [ ] 实现Server-Sent Events (SSE)
- [ ] 集成到聊天端点
- [ ] 编写流式响应测试
- [ ] 提交代码并推送到GitHub
- **验收标准**：流式响应正常，前端可接收

### 阶段七：CrewAI多智能体集成 (Phase 7: CrewAI Multi-Agent Integration)

#### 步骤 7.1: CrewAI服务实现
- [ ] 创建CrewAIService类（app/services/agents/crew_service.py）
- [ ] 实现智能体创建逻辑
- [ ] 实现任务执行逻辑
- [ ] 编写服务测试
- [ ] 提交代码并推送到GitHub
- **验收标准**：CrewAI服务可创建智能体团队

#### 步骤 7.2: 智能体API端点
- [ ] 实现GET /api/v1/projects/{project_id}/agents
- [ ] 实现POST /api/v1/projects/{project_id}/agents
- [ ] 实现智能体执行端点
- [ ] 编写完整测试
- [ ] 提交代码并推送到GitHub
- **验收标准**：智能体API功能完整，测试通过

### 阶段八：前端配置和API客户端 (Phase 8: Frontend Configuration)

#### 步骤 8.1: 前端环境配置
- [ ] 创建.env.local文件
- [ ] 配置API基础URL
- [ ] 修改next.config.mjs（端口3001）
- [ ] 创建统一API客户端
- [ ] 编写API客户端测试
- **验收标准**：前端可连接到后端API

#### 步骤 8.2: API调用迁移
- [ ] 替换所有API调用为新的后端端点
- [ ] 实现统一错误处理
- [ ] 更新TypeScript类型定义
- [ ] 测试所有API调用
- [ ] 提交代码并推送到GitHub
- **验收标准**：所有API调用正常，错误处理完善

### 阶段九：前端中文本地化 (Phase 9: Frontend Localization)

#### 步骤 9.1: 文本提取和翻译
- [ ] 扫描所有前端文件，提取英文文本
- [ ] 创建i18n语言文件
- [ ] 翻译所有用户可见文本
- [ ] 实现i18n系统
- [ ] 测试所有页面
- **验收标准**：所有文本已翻译，显示正常

#### 步骤 9.2: 品牌替换
- [ ] 替换所有"rowboat"相关文本为"质信智购"
- [ ] 替换Logo和品牌图片
- [ ] 更新所有引用
- [ ] 测试所有页面
- [ ] 提交代码并推送到GitHub
- **验收标准**：品牌替换完整，无遗漏

### 阶段十：完整功能测试 (Phase 10: Complete Testing)

#### 步骤 10.1: 集成测试
- [ ] 编写端到端测试
- [ ] 测试所有API端点
- [ ] 测试前端所有功能
- [ ] 修复发现的问题
- [ ] 提交代码并推送到GitHub
- **验收标准**：所有功能正常，测试通过

#### 步骤 10.2: 性能优化
- [ ] 性能测试
- [ ] 优化慢查询
- [ ] 优化API响应时间
- [ ] 优化前端加载速度
- [ ] 提交代码并推送到GitHub
- **验收标准**：性能指标达标

### 阶段十一：文档和部署准备 (Phase 11: Documentation & Deployment)

#### 步骤 11.1: 文档完善
- [ ] 更新README.md
- [ ] 编写API文档
- [ ] 编写部署文档
- [ ] 编写开发指南
- [ ] 提交代码并推送到GitHub
- **验收标准**：文档完整清晰

#### 步骤 11.2: 部署准备
- [ ] 创建Docker配置
- [ ] 创建docker-compose.yml
- [ ] 配置生产环境变量
- [ ] 测试部署流程
- [ ] 提交代码并推送到GitHub
- **验收标准**：可成功部署

## 开发原则（每步必须遵守）

1. **禁止硬编码**：所有配置、常量从环境变量或配置文件读取
2. **高度解耦**：新功能不影响旧功能，模块间低耦合
3. **测试驱动**：每步完成后编写测试，确保功能正常
4. **代码审查**：每步完成后审视代码，确保符合规范
5. **版本控制**：每完成一个步骤就提交并推送到GitHub
6. **文档同步**：代码变更时同步更新文档

## 验收检查清单（每步完成后检查）

- [ ] 代码符合项目规范（命名、结构、注释）
- [ ] 无硬编码值
- [ ] 配置外部化
- [ ] 测试通过（如适用）
- [ ] 代码已提交到GitHub
- [ ] 文档已更新（如适用）
- [ ] 不影响已有功能（如适用）

## 进度跟踪

使用TODO列表跟踪每个步骤的完成情况。每完成一个步骤，更新TODO状态并推送到GitHub。

---

**文档版本**：v1.0  
**创建日期**：2025-01-27  
**最后更新**：2025-01-27


