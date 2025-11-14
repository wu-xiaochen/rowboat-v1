# 质信智购后端 (ZhiXinZhiGou Backend)

## 技术栈

- **FastAPI**: 现代、快速的Web框架
- **LangChain**: Copilot核心框架
- **CrewAI**: 多智能体协作框架
- **MongoDB**: 主数据库
- **Redis**: 缓存和会话存储
- **Qdrant**: 向量数据库（RAG功能）

## 快速开始

### 1. 安装依赖

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写实际的配置值。

### 3. 启动服务

```bash
python main.py
```

服务将在 `http://localhost:8001` 启动。

## 项目结构

```
backend/
├── app/
│   ├── api/                 # API路由
│   │   └── v1/             # API版本1
│   │       └── endpoints/  # 具体端点
│   ├── core/               # 核心配置
│   │   └── config.py       # 配置管理
│   ├── services/           # 业务逻辑层
│   │   ├── copilot/        # Copilot服务（LangChain）
│   │   ├── agents/         # 智能体服务（CrewAI）
│   │   └── chat/           # 聊天服务
│   ├── models/             # 数据模型
│   ├── repositories/       # 数据访问层
│   └── workers/            # 后台任务
├── tests/                  # 测试文件
├── scripts/                # 工具脚本
├── requirements.txt        # Python依赖
├── .env.example           # 环境变量模板
└── main.py                # 应用入口
```

## 开发规范

请参考根目录的 `PROJECT-RULES.md` 和 `DEVELOPMENT-PLAN.md`。

## 测试

### 快速测试（不需要启动服务）
后端API测试使用 `ASGITransport`，不需要实际运行服务：

```bash
cd backend
python -m pytest tests/ -v --tb=short --timeout=60 --timeout-method=thread
```

### 完整测试（需要启动前后端服务）
使用测试脚本自动启动服务并运行测试：

```bash
./scripts/test_with_services.sh
```

更多测试信息请参考 [测试运行指南](../../docs/TESTING_WITH_SERVICES.md)。

## API文档

启动服务后访问：
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

