# 项目开发规则文档 (Project Rules)

## 1. 项目概述

### 1.1 项目目标
本项目旨在将现有的 Rowboat 项目进行前后端分离改造，完整保留前端的所有功能和设计，同时将后端完整替换为基于 Python 的现代化框架。

### 1.2 核心要求
- **前端**：保留所有设计、功能、布局，进行全面的中文本地化，将 "rowboat" 品牌替换为 "质信智购"
- **后端**：使用 Python 技术栈，LangChain 作为外层 Copilot 主框架，CrewAI 作为多智能体框架，FastAPI 作为 API 框架
- **架构**：前后端完全分离，通过 RESTful API 通信
- **配置**：所有配置外部化，禁止硬编码
- **代码质量**：目录结构清晰，及时清理无用文件

### 1.3 技术栈

#### 前端技术栈
- **框架**：Next.js 15.x
- **语言**：TypeScript
- **UI库**：React 19.x, HeroUI
- **样式**：Tailwind CSS
- **状态管理**：React Hooks
- **运行端口**：3001

#### 后端技术栈
- **API框架**：FastAPI
- **Copilot框架**：LangChain
- **多智能体框架**：CrewAI
- **数据库**：MongoDB, Redis, Qdrant
- **运行端口**：8001
- **Python版本**：Python 3.11+

## 2. 架构设计原则

### 2.1 前后端分离原则
1. **完全解耦**：前端和后端通过 HTTP API 通信，不共享任何代码
2. **API优先**：所有功能通过 RESTful API 暴露，API 设计遵循 OpenAPI 规范
3. **独立部署**：前端和后端可以独立部署和扩展
4. **CORS配置**：后端需要正确配置 CORS，允许前端域名访问

### 2.2 配置管理原则
1. **禁止硬编码**：所有配置值必须从环境变量或配置文件读取
2. **配置外部化**：使用 `.env` 文件或环境变量管理配置
3. **配置验证**：启动时验证所有必需配置项
4. **敏感信息保护**：API密钥等敏感信息不得提交到版本控制

### 2.3 代码组织原则
1. **清晰目录结构**：按功能模块组织代码，遵循框架最佳实践
2. **及时清理**：定期清理无用文件、过期文档、测试结果、缓存文件
3. **模块化设计**：功能模块化，低耦合高内聚
4. **可维护性**：代码注释清晰，命名规范统一

## 3. 前端开发规则

### 3.1 中文本地化要求

#### 3.1.1 文本替换规则
- 所有用户可见的英文文本必须翻译为中文
- 保持原有设计风格和布局不变
- 翻译要符合中文表达习惯，专业术语保持一致

#### 3.1.2 品牌替换规则
- **"rowboat" / "Rowboat" / "ROWBOAT"** → **"质信智购"**
- **"RowBoat Labs"** → **"质信智购"**
- 品牌相关的所有引用都需要替换
- Logo 和品牌图片需要替换（保留原有设计风格）

#### 3.1.3 国际化实现
- 使用 Next.js 的国际化功能或自定义 i18n 方案
- 所有文本内容提取到语言文件中
- 支持后续扩展多语言（如需要）

### 3.2 前端目录结构

```
apps/rowboat/
├── app/                          # Next.js App Router
│   ├── api/                      # 前端API代理（如需要）
│   ├── components/               # 组件
│   ├── lib/                      # 工具函数
│   ├── projects/                 # 项目相关页面
│   └── ...
├── components/                    # 共享组件
├── public/                       # 静态资源
│   ├── logo.png                 # 新品牌Logo
│   └── ...
├── styles/                       # 样式文件
├── .env.local                    # 前端环境变量
└── next.config.mjs               # Next.js配置
```

### 3.3 API调用规范
- 所有后端API调用使用统一的HTTP客户端
- API基础URL从环境变量读取：`NEXT_PUBLIC_API_BASE_URL=http://localhost:8001`
- 统一错误处理和响应格式
- 使用TypeScript类型定义API接口

### 3.4 前端配置

#### 3.4.1 环境变量（.env.local）
```bash
# API配置
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001

# 应用配置
NEXT_PUBLIC_APP_NAME=质信智购
NEXT_PUBLIC_PORT=3001
```

## 4. 后端开发规则

### 4.1 框架使用规范

#### 4.1.1 FastAPI规范
- 遵循FastAPI官方文档最佳实践：https://fastapi.tiangolo.com/
- 使用Pydantic进行数据验证
- API路由按功能模块组织
- 使用依赖注入管理服务
- 实现OpenAPI文档自动生成

#### 4.1.2 LangChain规范
- 遵循LangChain官方文档：https://python.langchain.com/
- LangChain作为Copilot的核心框架
- 使用LangChain的工具、链、代理等功能
- 保持与现有Copilot功能的兼容性

#### 4.1.3 CrewAI规范
- 遵循CrewAI官方文档：https://docs.crewai.com/
- CrewAI用于多智能体协作场景
- 智能体定义清晰，职责明确
- 智能体间通信使用标准协议

### 4.2 后端目录结构

```
backend/
├── app/
│   ├── api/                      # FastAPI路由
│   │   ├── v1/                   # API版本1
│   │   │   ├── endpoints/        # 具体端点
│   │   │   │   ├── chat.py
│   │   │   │   ├── projects.py
│   │   │   │   ├── agents.py
│   │   │   │   └── ...
│   │   │   └── __init__.py
│   │   └── dependencies.py       # 依赖注入
│   ├── core/                     # 核心配置
│   │   ├── config.py             # 配置管理
│   │   ├── security.py           # 安全相关
│   │   └── database.py           # 数据库连接
│   ├── services/                # 业务逻辑层
│   │   ├── copilot/              # Copilot服务（LangChain）
│   │   ├── agents/               # 智能体服务（CrewAI）
│   │   ├── chat/                 # 聊天服务
│   │   └── ...
│   ├── models/                   # 数据模型
│   │   ├── schemas.py            # Pydantic模型
│   │   └── database.py           # 数据库模型
│   ├── repositories/             # 数据访问层
│   │   ├── projects.py
│   │   ├── conversations.py
│   │   └── ...
│   └── workers/                  # 后台任务
│       ├── rag_worker.py
│       └── jobs_worker.py
├── tests/                        # 测试文件
├── scripts/                      # 工具脚本
├── .env                         # 环境变量
├── requirements.txt             # Python依赖
└── main.py                      # 应用入口
```

### 4.3 配置管理

#### 4.3.1 提示词配置管理
- **禁止硬编码提示词**：所有Copilot提示词必须从配置文件读取
- **提示词文件位置**：`backend/config/prompts/`
- **文件格式**：使用`.txt`或`.md`文件存储提示词
- **配置加载**：在启动时加载所有提示词到内存
- **提示词版本管理**：提示词文件纳入版本控制
- **提示词命名规范**：
  - `copilot_multi_agent.txt`：多智能体copilot核心指令
  - `copilot_edit_agent.txt`：agent编辑指令
  - `copilot_examples.txt`：示例
  - `current_workflow.txt`：当前工作流提示模板

#### 4.3.2 环境变量配置（.env）
```bash
# 应用配置
APP_NAME=质信智购
API_PORT=8001
DEBUG=false

# LLM Provider配置（OpenAI兼容）
LLM_API_KEY=sk-zueyelhrtzsngjdnqfnwfbsboockestuzwwhujpqrjmjmxyy
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL_ID=MiniMaxAI/MiniMax-M2

# Embedding配置
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_PROVIDER_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDING_PROVIDER_API_KEY=sk-zueyelhrtzsngjdnqfnwfbsboockestuzwwhujpqrjmjmxyy

# Composio配置
COMPOSIO_API_KEY=ak_KOSnpLA9q1ceJCjkKIKa

# 数据库配置
MONGODB_CONNECTION_STRING=mongodb://localhost:27017/zhixinzhigou
REDIS_URL=redis://localhost:6379
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# 其他配置
USE_RAG=true
USE_COMPOSIO_TOOLS=true
```

#### 4.3.3 配置加载规范
- 使用`pydantic-settings`管理配置
- 配置类定义在`app/core/config.py`
- 所有配置项必须有默认值或明确标记为必需
- 启动时验证配置完整性

#### 4.3.4 配置类示例
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 应用配置
    app_name: str = "质信智购"
    api_port: int = 8001
    debug: bool = False
    
    # LLM配置
    llm_api_key: str
    llm_base_url: str
    llm_model_id: str
    
    # Embedding配置
    embedding_model: str
    embedding_provider_base_url: str
    embedding_provider_api_key: str
    
    # Composio配置
    composio_api_key: str
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

### 4.4 API设计规范

#### 4.4.1 RESTful API设计
- 遵循RESTful设计原则
- 使用标准HTTP方法（GET, POST, PUT, DELETE）
- 统一的响应格式
- 版本控制：`/api/v1/...`

#### 4.4.2 API端点规范
```
POST   /api/v1/{project_id}/chat              # 聊天对话
GET    /api/v1/projects                       # 获取项目列表
POST   /api/v1/projects                       # 创建项目
GET    /api/v1/projects/{project_id}          # 获取项目详情
PUT    /api/v1/projects/{project_id}          # 更新项目
DELETE /api/v1/projects/{project_id}          # 删除项目
GET    /api/v1/projects/{project_id}/agents   # 获取智能体列表
POST   /api/v1/projects/{project_id}/agents   # 创建智能体
...
```

#### 4.4.3 响应格式规范
```python
# 成功响应
{
    "success": true,
    "data": {...},
    "message": "操作成功"
}

# 错误响应
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "错误描述",
        "details": {...}
    }
}
```

### 4.5 LangChain集成规范

#### 4.5.1 Copilot服务实现
- 使用LangChain的Agent框架
- 支持工具调用（Tools）
- 支持RAG（检索增强生成）
- 支持流式响应

#### 4.5.2 代码组织
```python
# app/services/copilot/copilot_service.py
from langchain.agents import AgentExecutor
from langchain.tools import Tool
from langchain.llms import OpenAI

class CopilotService:
    def __init__(self, config: Settings):
        # 初始化LangChain组件
        pass
    
    async def process_message(self, message: str, context: dict):
        # 处理用户消息
        pass
```

### 4.6 CrewAI集成规范

#### 4.6.1 多智能体实现
- 使用CrewAI创建智能体团队
- 定义清晰的智能体角色和任务
- 实现智能体间的协作流程

#### 4.6.2 代码组织
```python
# app/services/agents/crew_service.py
from crewai import Agent, Task, Crew

class CrewAIService:
    def __init__(self, config: Settings):
        # 初始化CrewAI组件
        pass
    
    async def create_crew(self, agents_config: list):
        # 创建智能体团队
        pass
    
    async def execute_task(self, crew: Crew, task: str):
        # 执行任务
        pass
```

## 5. 数据库和存储

### 5.1 MongoDB规范
- 使用Motor（异步MongoDB驱动）
- 数据库名称：`zhixinzhigou`
- 集合命名使用复数形式（如：`projects`, `conversations`）
- 使用索引优化查询性能

### 5.2 Redis规范
- 用于缓存和会话存储
- 使用`redis`或`aioredis`异步客户端
- 设置合理的过期时间

### 5.3 Qdrant规范
- 用于向量存储（RAG功能）
- 使用`qdrant-client`库
- 集合命名规范：`{project_id}_vectors`

## 6. 代码质量规范

### 6.1 Python代码规范
- 遵循PEP 8代码风格
- 使用类型提示（Type Hints）
- 函数和类必须有文档字符串
- 使用`black`进行代码格式化
- 使用`ruff`或`flake8`进行代码检查

### 6.2 TypeScript代码规范
- 遵循ESLint规则
- 使用严格的TypeScript配置
- 组件必须有类型定义
- 使用Prettier进行代码格式化

### 6.3 注释规范
- 所有公共函数和类必须有文档字符串
- 复杂逻辑必须有行内注释
- 使用中文注释（业务逻辑）或英文注释（技术实现）

### 6.4 命名规范
- **Python**：使用snake_case（函数、变量），PascalCase（类）
- **TypeScript**：使用camelCase（函数、变量），PascalCase（类、组件）
- **数据库**：使用snake_case
- **API端点**：使用kebab-case

## 7. 测试规范

### 7.1 测试要求
- 关键业务逻辑必须有单元测试
- API端点必须有集成测试
- 测试覆盖率目标：>70%

### 7.2 测试组织
```
tests/
├── unit/                    # 单元测试
├── integration/             # 集成测试
└── fixtures/                # 测试数据
```

### 7.3 测试运行
- 使用`pytest`运行Python测试
- 使用`jest`运行前端测试
- CI/CD中自动运行测试

## 8. 文件清理规范

### 8.1 定期清理内容
- **测试结果**：`.pytest_cache/`, `coverage/`, `test-results/`
- **构建产物**：`dist/`, `build/`, `.next/`（保留.gitignore）
- **缓存文件**：`__pycache__/`, `.mypy_cache/`, `.ruff_cache/`
- **临时文件**：`*.tmp`, `*.log`（开发日志）
- **过期文档**：过时的README、过期的设计文档

### 8.2 清理脚本
创建清理脚本：`scripts/cleanup.sh` 或 `scripts/cleanup.py`

### 8.3 .gitignore规范
确保以下内容在`.gitignore`中：
```
# Python
__pycache__/
*.py[cod]
.pytest_cache/
.coverage
.mypy_cache/
.ruff_cache/

# Node.js
node_modules/
.next/
dist/
*.log

# 环境变量
.env
.env.local

# IDE
.vscode/
.idea/

# 临时文件
*.tmp
*.swp
```

## 9. 开发流程

### 9.1 开发环境设置
1. 克隆项目
2. 安装依赖（前端：`npm install`，后端：`pip install -r requirements.txt`）
3. 配置环境变量（复制`.env.example`到`.env`并填写）
4. 启动数据库服务（MongoDB, Redis, Qdrant）
5. 运行数据库迁移（如需要）
6. 启动开发服务器

### 9.2 开发命令
```bash
# 前端开发
cd apps/rowboat
npm run dev  # 运行在3001端口

# 后端开发
cd backend
uvicorn app.main:app --reload --port 8001
```

### 9.3 代码提交规范
- 使用有意义的提交信息
- 遵循Conventional Commits规范
- 每次提交前运行测试和代码检查

## 10. 部署规范

### 10.1 环境配置
- **开发环境**：localhost
- **测试环境**：独立的测试服务器
- **生产环境**：生产服务器配置

### 10.2 Docker部署
- 前端和后端分别构建Docker镜像
- 使用docker-compose编排服务
- 环境变量通过docker-compose或Kubernetes配置

### 10.3 端口配置
- **前端**：3001
- **后端**：8001
- **MongoDB**：27017
- **Redis**：6379
- **Qdrant**：6333

## 11. 安全规范

### 11.1 API安全
- **API Key验证**：所有API端点需要验证API Key（从请求头Authorization: Bearer {key}读取）
- **项目Secret**：每个项目生成唯一secret用于webhook验证
- **用户认证**：可选使用JWT或Auth0进行用户身份验证
- **速率限制**：实现Rate Limiting防止滥用
- **输入验证**：使用Pydantic进行严格的输入验证
- **SQL注入防护**：使用参数化查询（MongoDB、Redis）

### 11.2 数据安全
- 敏感数据加密存储
- 使用HTTPS传输
- 定期备份数据库

## 12. 文档规范

### 12.1 代码文档
- API文档使用FastAPI自动生成（Swagger UI）
- 代码注释清晰完整
- README文件保持更新

### 12.2 项目文档
- 架构设计文档
- API接口文档
- 部署文档
- 开发指南

## 13. 参考资源

### 13.1 官方文档
- **FastAPI**：https://fastapi.tiangolo.com/
- **LangChain**：https://python.langchain.com/
- **CrewAI**：https://docs.crewai.com/
- **Next.js**：https://nextjs.org/docs
- **MongoDB**：https://www.mongodb.com/docs/
- **Qdrant**：https://qdrant.tech/documentation/

### 13.2 开发工具
- **Python格式化**：black, ruff
- **TypeScript格式化**：prettier, eslint
- **API测试**：Postman, Insomnia
- **数据库管理**：MongoDB Compass, Redis Insight

## 14. 项目里程碑

### 阶段一：基础架构搭建
- [ ] 后端FastAPI项目初始化
- [ ] 配置管理系统实现
- [ ] 数据库连接和基础Repository
- [ ] 基础API端点实现

### 阶段二：核心功能迁移
- [ ] LangChain Copilot服务实现
- [ ] CrewAI多智能体框架集成
- [ ] 聊天API完整实现
- [ ] 项目管理API实现

### 阶段三：前端改造
- [ ] 前端中文本地化
- [ ] 品牌替换（rowboat → 质信智购）
- [ ] API调用迁移到新后端
- [ ] 功能测试和修复

### 阶段四：优化和测试
- [ ] 性能优化
- [ ] 完整测试覆盖
- [ ] 文档完善
- [ ] 部署准备

## 15. 注意事项

1. **禁止硬编码**：所有配置、常量、URL等必须从配置文件或环境变量读取
2. **保持兼容**：API设计尽量保持与现有前端兼容，减少前端改动
3. **渐进式迁移**：可以分模块逐步迁移，确保每个模块稳定后再继续
4. **测试驱动**：关键功能必须有测试覆盖
5. **代码审查**：重要变更必须经过代码审查
6. **文档同步**：代码变更时同步更新文档

---

**文档版本**：v1.0  
**最后更新**：2025-01-27  
**维护者**：开发团队

