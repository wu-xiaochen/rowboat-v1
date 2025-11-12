# 配置文件位置
# Configuration Files Location

**最后更新**：2025-01-27

## 📁 配置文件位置

### 后端配置

**配置文件**：`backend/.env`
- 包含所有后端API密钥和数据库连接信息
- 已配置所有必需项 ✅

**配置类**：`backend/app/core/config.py`
- Python配置类定义
- 使用 `pydantic-settings` 管理

### 前端配置

**配置文件**：`apps/rowboat/.env.local`
- 包含前端环境变量
- 已配置所有必需项 ✅

**配置代码位置**：
- API客户端：`apps/rowboat/src/application/lib/api-client.ts`
- Composio客户端：`apps/rowboat/src/application/lib/composio/composio.ts`

## 🔑 已配置的密钥

### 后端 (.env)
- ✅ LLM API Key: sk-zueyelhrtzsngjdnqfnwfbsboockestuzwwhujpqrjmjmxyy
- ✅ LLM Base URL: https://api.siliconflow.cn/v1
- ✅ LLM Model: MiniMaxAI/MiniMax-M2
- ✅ Embedding配置: 已配置
- ✅ Composio API Key: ak_KOSnpLA9q1ceJCjkKIKa
- ✅ MongoDB: mongodb://localhost:27017/zhixinzhigou
- ✅ Redis: redis://localhost:6379
- ✅ Qdrant: http://localhost:6333

### 前端 (.env.local)
- ✅ API Base URL: http://localhost:8001
- ✅ Composio API Key: ak_KOSnpLA9q1ceJCjkKIKa
- ✅ 应用名称: 质信智购
- ✅ 端口: 3001

## 🚀 启动服务

### 启动后端
```bash
cd backend
python main.py
```
或
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 启动前端
```bash
cd apps/rowboat
npm run dev
```

## 📚 相关文档

- `CONFIGURATION_GUIDE.md` - 详细配置管理指南
- `QUICK_START.md` - 快速启动指南

---

**注意**：`.env` 和 `.env.local` 文件已被 `.gitignore` 保护，不会提交到版本控制。
