# 快速启动指南
# Quick Start Guide

**最后更新**：2025-01-27

## 📋 前置要求

- Node.js 18+ 和 npm
- Python 3.11+
- MongoDB（本地或远程）
- Redis（本地或远程）
- Qdrant（本地或远程，可选，用于RAG功能）

## ⚙️ 配置环境变量

### 统一配置文件

项目使用**统一配置文件**管理环境变量，配置文件位于项目根目录：

**主要配置文件**：`.env`（项目根目录）

```bash
# 如果还没有 .env 文件，可以从 .env.example 复制
cp .env.example .env

# 编辑 .env 文件，填写你的配置
```

### 必需配置项

```bash
# LLM Provider配置（必需）
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL_ID=MiniMaxAI/MiniMax-M2

# 数据库配置（必需）
MONGODB_CONNECTION_STRING=mongodb://localhost:27017/zhixinzhigou
REDIS_URL=redis://localhost:6379
QDRANT_URL=http://localhost:6333

# Composio配置（可选，用于工具集成）
COMPOSIO_API_KEY=your-composio-api-key
```

### 配置加载优先级

- **前端**：`apps/rowboat/.env.local` > 根目录 `.env` > `apps/rowboat/.env`
- **后端**：根目录 `.env` > `backend/.env` > `.env`

> 💡 **提示**：主要配置放在根目录 `.env` 文件中，个人本地覆盖使用 `.env.local`（不会被提交到Git）

## 🚀 启动服务

### 方式一：使用启动脚本（推荐）

```bash
# 启动所有服务（包括数据库）
./start.sh
```

### 方式二：手动启动

#### 1. 启动数据库服务

确保以下服务已启动：
- MongoDB: `mongodb://localhost:27017`
- Redis: `redis://localhost:6379`
- Qdrant: `http://localhost:6333`（可选）

#### 2. 启动后端服务

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**后端服务地址**：
- API: http://localhost:8001
- API文档: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

#### 3. 启动前端服务

```bash
cd apps/rowboat
npm install  # 首次运行需要安装依赖
npm run dev
```

**前端服务地址**：http://localhost:3001

## ✅ 验证服务

### 检查后端服务

```bash
# 健康检查
curl http://localhost:8001/api/v1/health

# 查看API信息
curl http://localhost:8001/api/v1/info
```

### 检查前端服务

打开浏览器访问：http://localhost:3001

## 🛠️ 常用命令

### 停止服务

**停止后端**：
```bash
lsof -ti:8001 | xargs kill -9
```

**停止前端**：
```bash
lsof -ti:3001 | xargs kill -9
```

### 查看日志

**后端日志**：
```bash
tail -f /tmp/backend.log
```

**前端日志**：
```bash
tail -f /tmp/frontend.log
```

### 清理缓存

```bash
# 清理 Python 缓存
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name ".pytest_cache" -exec rm -rf {} +

# 清理前端构建缓存
cd apps/rowboat
rm -rf .next
```

## 📝 配置说明

### 完整配置项

查看 [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) 了解所有配置项的详细说明。

### 主要配置项

| 配置项 | 说明 | 必需 |
|--------|------|------|
| `LLM_API_KEY` | LLM服务API密钥 | ✅ |
| `LLM_BASE_URL` | LLM服务基础URL | ✅ |
| `LLM_MODEL_ID` | LLM模型ID | ✅ |
| `MONGODB_CONNECTION_STRING` | MongoDB连接字符串 | ✅ |
| `REDIS_URL` | Redis连接URL | ✅ |
| `COMPOSIO_API_KEY` | Composio API密钥 | ❌ |

## ⚠️ 注意事项

1. **数据库服务**：确保MongoDB、Redis、Qdrant服务已启动
2. **端口占用**：确保8001和3001端口未被占用
3. **环境变量**：配置文件已统一到根目录 `.env`，便于维护
4. **敏感信息**：`.env.local` 文件不会被提交到Git，适合存放个人配置

## 🔗 相关文档

- [配置指南](CONFIGURATION_GUIDE.md) - 详细的配置说明
- [开发计划](DEVELOPMENT-PLAN.md) - 项目开发计划
- [认证和授权](AUTHENTICATION_AND_AUTHORIZATION.md) - 认证系统说明

---

**配置文件位置**：
- 主要配置：项目根目录 `.env`
- 本地覆盖：`apps/rowboat/.env.local`（可选）
- 向后兼容：`backend/.env`（可选）
