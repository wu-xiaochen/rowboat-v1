# 配置管理指南
# Configuration Management Guide

**创建日期**：2025-01-27  
**目的**：统一管理项目配置，避免配置分散

## 配置管理原则

1. **禁止硬编码**：所有配置值必须从环境变量或配置文件读取
2. **配置外部化**：使用 `.env` 文件或环境变量管理配置
3. **配置验证**：启动时验证所有必需配置项
4. **敏感信息保护**：API密钥等敏感信息不得提交到版本控制

## 后端配置

### 配置文件位置
- **主配置**：`backend/app/core/config.py`
- **环境变量文件**：`backend/.env`

### 配置类
使用 `pydantic-settings` 的 `BaseSettings` 类管理所有配置：

```python
from app.core.config import get_settings

settings = get_settings()
```

### 必需的环境变量

```bash
# LLM Provider配置（OpenAI兼容）
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL_ID=MiniMaxAI/MiniMax-M2

# Embedding配置
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_PROVIDER_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDING_PROVIDER_API_KEY=sk-xxx

# Composio配置
COMPOSIO_API_KEY=ak_xxx

# 数据库配置
MONGODB_CONNECTION_STRING=mongodb://localhost:27017/zhixinzhigou
REDIS_URL=redis://localhost:6379
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# 功能开关
USE_RAG=true
USE_COMPOSIO_TOOLS=true
```

### 配置验证
启动时会自动验证所有必需配置项，缺失配置会抛出异常。

## 前端配置

### 配置文件位置
- **环境变量文件**：`apps/rowboat/.env.local`
- **API客户端**：`apps/rowboat/src/application/lib/api-client.ts`
- **Composio客户端**：`apps/rowboat/src/application/lib/composio/composio.ts`

### 必需的环境变量

```bash
# API配置
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001

# Composio配置
NEXT_PUBLIC_COMPOSIO_API_KEY=ak_xxx

# 应用配置
NEXT_PUBLIC_APP_NAME=质信智购
NEXT_PUBLIC_PORT=3001
```

### 配置使用

#### API基础URL
```typescript
// apps/rowboat/src/application/lib/api-client.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001';
```

#### Composio API Key
```typescript
// apps/rowboat/src/application/lib/composio/composio.ts
const COMPOSIO_API_KEY = 
  process.env.NEXT_PUBLIC_COMPOSIO_API_KEY || 
  process.env.COMPOSIO_API_KEY || 
  'test';
```

### 配置说明
- `NEXT_PUBLIC_` 前缀：Next.js约定，用于在客户端代码中暴露环境变量
- 默认值：提供合理的默认值，但生产环境必须配置
- 类型安全：使用TypeScript确保配置类型正确

## 配置统一性检查

### ✅ 后端配置
- ✅ 所有配置统一在 `backend/app/core/config.py`
- ✅ 使用 `pydantic-settings` 管理
- ✅ 配置验证机制完善
- ✅ 无硬编码配置值

### ✅ 前端配置
- ✅ API基础URL统一在 `api-client.ts`
- ✅ Composio配置统一在 `composio.ts`
- ✅ 使用环境变量管理
- ✅ 提供合理的默认值

## 配置最佳实践

### 1. 环境变量命名
- **后端**：使用大写字母和下划线，如 `LLM_API_KEY`
- **前端**：使用 `NEXT_PUBLIC_` 前缀，如 `NEXT_PUBLIC_API_BASE_URL`

### 2. 默认值
- 提供合理的默认值（开发环境）
- 生产环境必须明确配置
- 敏感信息不得有默认值

### 3. 配置验证
- 启动时验证必需配置
- 提供清晰的错误消息
- 记录缺失的配置项

### 4. 文档化
- 在README中说明必需配置
- 提供 `.env.example` 模板
- 文档中说明配置用途

## 配置模板

### 后端 `.env.example`
```bash
# 应用配置
APP_NAME=质信智购
API_PORT=8001
DEBUG=false

# LLM Provider配置
LLM_API_KEY=your-llm-api-key
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL_ID=MiniMaxAI/MiniMax-M2

# Embedding配置
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_PROVIDER_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDING_PROVIDER_API_KEY=your-embedding-api-key

# Composio配置
COMPOSIO_API_KEY=your-composio-api-key

# 数据库配置
MONGODB_CONNECTION_STRING=mongodb://localhost:27017/zhixinzhigou
REDIS_URL=redis://localhost:6379
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# 功能开关
USE_RAG=true
USE_COMPOSIO_TOOLS=true
```

### 前端 `.env.local.example`
```bash
# API配置
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001

# Composio配置
NEXT_PUBLIC_COMPOSIO_API_KEY=your-composio-api-key

# 应用配置
NEXT_PUBLIC_APP_NAME=质信智购
NEXT_PUBLIC_PORT=3001
```

## 配置检查清单

### 开发环境
- [ ] 后端 `.env` 文件已配置
- [ ] 前端 `.env.local` 文件已配置
- [ ] 所有必需配置项已填写
- [ ] 配置验证通过

### 生产环境
- [ ] 环境变量已设置
- [ ] 敏感信息已保护
- [ ] 配置已文档化
- [ ] 配置备份策略已制定

## 常见问题

### Q: 如何添加新配置？
A: 
1. 在 `backend/app/core/config.py` 中添加配置字段
2. 在 `.env.example` 中添加示例值
3. 更新本文档

### Q: 前端配置在哪里管理？
A: 
- API配置：`apps/rowboat/src/application/lib/api-client.ts`
- Composio配置：`apps/rowboat/src/application/lib/composio/composio.ts`
- 其他配置：使用 `process.env.NEXT_PUBLIC_*`

### Q: 如何验证配置？
A: 
- 后端：启动时会自动验证
- 前端：检查环境变量是否正确加载

---

**维护者**：开发团队  
**最后更新**：2025-01-27

