# 环境变量配置迁移指南

## 概述

为了简化配置管理，避免配置歧义，我们统一使用 `LLM_*` 前缀的环境变量，移除了向后兼容的 `PROVIDER_*` 前缀配置。

## 配置变更

### 移除的配置项

以下配置项已被移除，请从 `.env` 文件中删除：

```bash
# ❌ 已移除 - 向后兼容配置
PROVIDER_API_KEY=...
PROVIDER_BASE_URL=...
PROVIDER_DEFAULT_MODEL=...
PROVIDER_COPILOT_MODEL=...
```

### 标准配置项

统一使用以下标准配置：

```bash
# ✅ LLM Provider配置（OpenAI兼容）- 基础配置
LLM_API_KEY=sk-...
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL_ID=MiniMaxAI/MiniMax-M2

# ✅ Copilot和Agent模型配置（可选，用于区分不同场景的模型）
# 如果未设置，将自动使用 LLM_MODEL_ID
COPILOT_MODEL=MiniMaxAI/MiniMax-M2  # Copilot专用模型（可选）
AGENT_MODEL=MiniMaxAI/MiniMax-M2    # 智能体默认模型（可选）

# ✅ Embedding配置（统一使用 EMBEDDING_* 前缀）
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDING_API_KEY=sk-...

# ✅ 其他配置保持不变
COMPOSIO_API_KEY=...
MONGODB_CONNECTION_STRING=...
REDIS_URL=...
QDRANT_URL=...
```

## 自动清理脚本

运行以下脚本自动清理 `.env` 文件：

```bash
./scripts/cleanup-env-config.sh
```

脚本会：
1. 自动备份 `.env` 文件
2. 移除所有 `PROVIDER_*` 前缀的配置（向后兼容配置）
3. 注意：`COPILOT_MODEL` 和 `AGENT_MODEL` 现在保留，用于区分不同场景的模型

## 代码变更

### 后端

- `backend/app/core/config.py`: 移除了向后兼容逻辑，只从项目根目录的 `.env` 文件读取配置
- `backend/app/services/copilot/copilot_service.py`: 使用 `effective_copilot_model` 属性，自动回退到 `llm_model_id`

### 前端

- `apps/rowboat/src/application/lib/copilot/copilot.ts`: 统一使用 `LLM_*` 前缀
- `apps/rowboat/src/application/lib/agents-runtime/agents.ts`: 统一使用 `LLM_*` 前缀

## 模型配置说明

### 模型配置层级

1. **基础模型** (`LLM_MODEL_ID`): 默认模型，所有组件的基础配置
2. **Copilot模型** (`COPILOT_MODEL`): Copilot专用模型（可选）
   - 如果未设置，将自动使用 `LLM_MODEL_ID`
   - 允许为 Copilot 功能使用不同的模型
3. **智能体模型** (`AGENT_MODEL`): 智能体默认模型（可选）
   - 如果未设置，将自动使用 `LLM_MODEL_ID`
   - 允许为智能体使用不同的模型

### 配置示例

```bash
# 场景1: 所有组件使用同一个模型
LLM_MODEL_ID=MiniMaxAI/MiniMax-M2
# COPILOT_MODEL 和 AGENT_MODEL 不设置，自动使用 LLM_MODEL_ID

# 场景2: Copilot 和 Agent 使用不同模型
LLM_MODEL_ID=MiniMaxAI/MiniMax-M2          # 默认模型
COPILOT_MODEL=MiniMaxAI/MiniMax-M2         # Copilot专用
AGENT_MODEL=Qwen/Qwen2.5-72B-Instruct      # Agent专用
```

这样可以灵活地为不同场景配置不同的模型，同时保持配置的简洁性。

## 验证

清理配置后，请验证：

1. 后端服务能正常启动
2. Copilot 功能正常工作
3. 智能体功能正常工作
4. 检查日志确认使用的模型名称正确

