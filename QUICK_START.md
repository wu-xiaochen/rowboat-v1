# 快速启动指南
# Quick Start Guide

**最后更新**：2025-01-27

## 配置文件位置

### 后端配置
- **配置文件**：`backend/.env`
- **配置类**：`backend/app/core/config.py`
- **已配置**：✅ 所有API密钥和连接信息已配置

### 前端配置
- **配置文件**：`apps/rowboat/.env.local`
- **API客户端**：`apps/rowboat/src/application/lib/api-client.ts`
- **已配置**：✅ 所有环境变量已配置

## 启动服务

### 1. 启动后端服务

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

或者使用：
```bash
cd backend
python main.py
```

**后端服务地址**：http://localhost:8001
**API文档**：http://localhost:8001/docs

### 2. 启动前端服务

```bash
cd apps/rowboat
npm run dev
```

**前端服务地址**：http://localhost:3001

## 配置信息

### 后端配置（backend/.env）
- ✅ LLM API Key: 已配置
- ✅ LLM Base URL: https://api.siliconflow.cn/v1
- ✅ LLM Model: MiniMaxAI/MiniMax-M2
- ✅ Embedding配置: 已配置
- ✅ Composio API Key: 已配置
- ✅ MongoDB: mongodb://localhost:27017/zhixinzhigou
- ✅ Redis: redis://localhost:6379
- ✅ Qdrant: http://localhost:6333

### 前端配置（apps/rowboat/.env.local）
- ✅ API Base URL: http://localhost:8001
- ✅ Composio API Key: 已配置
- ✅ 应用名称: 质信智购
- ✅ 端口: 3001

## 验证服务

### 检查后端服务
```bash
curl http://localhost:8001/api/v1/health
```

### 检查前端服务
打开浏览器访问：http://localhost:3001

## 注意事项

1. **数据库服务**：确保MongoDB、Redis、Qdrant服务已启动
2. **端口占用**：确保8001和3001端口未被占用
3. **环境变量**：配置文件已创建，无需额外配置

## 停止服务

### 停止后端
按 `Ctrl+C` 或查找进程：
```bash
lsof -ti:8001 | xargs kill
```

### 停止前端
按 `Ctrl+C` 或查找进程：
```bash
lsof -ti:3001 | xargs kill
```

---

**配置文件位置**：
- 后端：`backend/.env`
- 前端：`apps/rowboat/.env.local`

**详细配置说明**：查看 `CONFIGURATION_GUIDE.md`

