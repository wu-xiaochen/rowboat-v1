# 配置管理指南
# Configuration Management Guide

**最后更新**：2025-01-27  
**目的**：统一管理项目配置，避免配置分散

## 📁 配置文件结构

项目使用**统一配置文件**管理环境变量：

```
rowboat/
├── .env                    # ✅ 统一配置文件（主要维护）
├── apps/rowboat/
│   └── .env.local          # 本地覆盖配置（可选，不提交Git）
└── backend/
    └── .env                # 向后兼容配置（可选）
```

## 🔧 配置加载优先级

### 前端（Next.js）
1. `apps/rowboat/.env.local` - 本地覆盖（最高优先级）
2. 根目录 `.env` - 统一配置
3. `apps/rowboat/.env` - 向后兼容

### 后端（FastAPI）
1. 根目录 `.env` - 统一配置
2. `backend/.env` - 向后兼容
3. `.env` - 当前目录

## ⚙️ 统一配置文件（.env）

**位置**：项目根目录 `.env`

这是项目的主要配置文件，包含前后端共享的所有配置。

### 必需配置项

```bash
# ============================================
# LLM Provider配置（OpenAI兼容）
# ============================================
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL_ID=MiniMaxAI/MiniMax-M2

# 兼容旧的环境变量名（向后兼容）
PROVIDER_API_KEY=${LLM_API_KEY}
PROVIDER_BASE_URL=${LLM_BASE_URL}
PROVIDER_DEFAULT_MODEL=${LLM_MODEL_ID}
PROVIDER_COPILOT_MODEL=${LLM_MODEL_ID}

# ============================================
# Embedding配置
# ============================================
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_PROVIDER_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDING_PROVIDER_API_KEY=your-api-key

# ============================================
# Composio配置（可选）
# ============================================
COMPOSIO_API_KEY=your-composio-api-key

# ============================================
# 数据库配置
# ============================================
MONGODB_CONNECTION_STRING=mongodb://localhost:27017/zhixinzhigou
REDIS_URL=redis://localhost:6379
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# ============================================
# 应用配置
# ============================================
APP_NAME=质信智购
API_PORT=8001
DEBUG=false
ENVIRONMENT=development

# ============================================
# 功能开关
# ============================================
USE_RAG=true
USE_COMPOSIO_TOOLS=true

# ============================================
# CORS配置
# ============================================
CORS_ORIGINS=http://localhost:3001,http://localhost:3000

# ============================================
# 前端专用配置（Next.js 需要 NEXT_PUBLIC_ 前缀）
# ============================================
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001
NEXT_PUBLIC_COMPOSIO_API_KEY=${COMPOSIO_API_KEY}
NEXT_PUBLIC_APP_NAME=${APP_NAME}
NEXT_PUBLIC_PORT=3001
```

## 🔐 本地覆盖配置（.env.local）

**位置**：`apps/rowboat/.env.local`

用于个人本地开发环境的配置覆盖，**不会被提交到Git**。

### 使用场景

- 个人API密钥
- 本地数据库连接
- 开发环境特定配置

### 示例

```bash
# 覆盖LLM配置
LLM_API_KEY=my-personal-api-key

# 覆盖数据库连接
MONGODB_CONNECTION_STRING=mongodb://localhost:27017/my-dev-db
```

## 📝 配置管理原则

1. **禁止硬编码**：所有配置值必须从环境变量或配置文件读取
2. **配置外部化**：使用 `.env` 文件管理配置
3. **统一管理**：主要配置放在根目录 `.env` 文件中
4. **本地覆盖**：个人配置使用 `.env.local`（不提交Git）
5. **配置验证**：启动时验证所有必需配置项
6. **敏感信息保护**：API密钥等敏感信息不得提交到版本控制

## 🔍 配置验证

### 后端配置验证

后端启动时会自动验证配置：

```python
from app.core.config import get_settings

settings = get_settings()
settings.validate_config()  # 验证配置完整性
```

### 前端配置验证

前端在 `loadenv.ts` 中加载配置，Next.js 会自动处理环境变量。

## 🛠️ 配置访问

### 后端访问配置

```python
from app.core.config import get_settings

settings = get_settings()
api_key = settings.llm_api_key
base_url = settings.llm_base_url
```

### 前端访问配置

**服务端代码**：
```typescript
const apiKey = process.env.LLM_API_KEY;
```

**客户端代码**（需要 `NEXT_PUBLIC_` 前缀）：
```typescript
const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
```

## 📋 配置项说明

### LLM配置

| 配置项 | 说明 | 必需 |
|--------|------|------|
| `LLM_API_KEY` | LLM服务API密钥 | ✅ |
| `LLM_BASE_URL` | LLM服务基础URL | ✅ |
| `LLM_MODEL_ID` | LLM模型ID | ✅ |

### 数据库配置

| 配置项 | 说明 | 必需 |
|--------|------|------|
| `MONGODB_CONNECTION_STRING` | MongoDB连接字符串 | ✅ |
| `REDIS_URL` | Redis连接URL | ✅ |
| `QDRANT_URL` | Qdrant连接URL | ✅ |
| `QDRANT_API_KEY` | Qdrant API密钥 | ❌ |

### 应用配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `APP_NAME` | 应用名称 | 质信智购 |
| `API_PORT` | 后端API端口 | 8001 |
| `DEBUG` | 调试模式 | false |
| `ENVIRONMENT` | 运行环境 | development |

## 🚀 快速配置

### 首次配置

1. 复制配置模板：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，填写你的配置值

3. 如需本地覆盖，创建 `.env.local`：
   ```bash
   cd apps/rowboat
   touch .env.local
   # 编辑 .env.local，添加个人配置
   ```

### 更新配置

直接编辑根目录的 `.env` 文件，重启服务后生效。

## ⚠️ 注意事项

1. **不要提交敏感信息**：`.env` 和 `.env.local` 都在 `.gitignore` 中
2. **使用 .env.example**：作为配置模板，可以提交到Git
3. **统一管理**：主要配置放在根目录 `.env`，便于团队协作
4. **本地覆盖**：个人配置使用 `.env.local`，不影响团队

## 🔗 相关文档

- [快速启动指南](QUICK_START.md) - 启动和配置说明
- [开发计划](DEVELOPMENT-PLAN.md) - 项目开发计划
- [项目规则](.cursor/rules/project-rules.mdc) - 开发规范

---

**配置文件位置**：
- 主要配置：项目根目录 `.env`
- 本地覆盖：`apps/rowboat/.env.local`（可选）
- 向后兼容：`backend/.env`（可选）
