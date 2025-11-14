# 测试框架使用指南
# Testing Framework Usage Guide

## 快速开始

### 1. 运行快速测试

```bash
# 验证服务状态和基础功能
./scripts/quick_test.sh
```

### 2. 运行手动API测试

```bash
# 不依赖pytest的API测试
./scripts/test_api_manually.sh
```

### 3. 检查遗留代码

```bash
# 检查前端遗留代码
./scripts/check_legacy_code.sh
```

## 完整测试套件

### 前提条件

1. **后端服务运行中** (http://localhost:8001)
2. **前端服务运行中** (http://localhost:3001)
3. **数据库服务运行中** (MongoDB, Redis, Qdrant)

### 安装测试依赖

#### 后端测试依赖

```bash
cd backend

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements-test.txt
```

#### 前端测试依赖

```bash
cd apps/rowboat

# 安装Playwright
npm install -D @playwright/test playwright
npx playwright install chromium
```

### 运行测试

#### 运行所有测试

```bash
# 完整测试套件
./scripts/comprehensive_test_and_fix.sh
```

#### 运行特定测试

```bash
# 后端API测试
cd backend
pytest tests/test_api_endpoints_comprehensive.py -v

# 服务层测试
pytest tests/test_services.py -v

# Playwright端到端测试
./scripts/run_playwright_tests.sh
```

## 测试文件结构

```
backend/tests/
├── test_api_endpoints_comprehensive.py  # 完整API端点测试
├── test_services.py                      # 服务层测试
└── test_frontend_legacy_code.py          # 遗留代码检查

tests/e2e/
├── test_full_workflow.spec.ts           # 工作流测试
└── test_complete_user_flows.spec.ts     # 完整用户流程测试

scripts/
├── quick_test.sh                        # 快速测试
├── test_api_manually.sh                # 手动API测试
├── run_basic_tests.sh                   # 基础测试
├── run_full_test_suite.sh               # 完整测试套件
├── run_playwright_tests.sh              # Playwright测试
├── check_legacy_code.sh                # 遗留代码检查
└── comprehensive_test_and_fix.sh       # 全面测试和修复
```

## 测试覆盖

### 后端API端点

- ✅ 健康检查 (`/api/v1/health`, `/api/v1/ping`)
- ✅ API信息 (`/api/v1/info`)
- ⏳ 项目管理 (`/api/v1/projects/*`)
- ⏳ 聊天 (`/api/v1/{project_id}/chat`)
- ⏳ Copilot (`/api/v1/{project_id}/copilot/*`)
- ⏳ API密钥 (`/api/v1/{project_id}/api-keys/*`)

### 服务层

- ⏳ Copilot服务
- ⏳ 智能体服务
- ⏳ 聊天服务

### 端到端测试

- ⏳ 创建智能体并测试对话
- ⏳ 使用Copilot创建智能体
- ⏳ 创建多个智能体并配置Pipeline
- ⏳ 添加工具并测试
- ⏳ 发布项目并使用
- ⏳ 编辑智能体配置
- ⏳ 删除智能体

## 测试报告

测试结果保存在：
- `test_results_YYYYMMDD_HHMMSS.txt` - 文本格式测试结果
- `playwright-report/index.html` - Playwright HTML报告
- `backend/.pytest_cache/` - pytest缓存

## 故障排除

### pytest未安装

```bash
# 使用虚拟环境
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-test.txt
```

### 服务未运行

```bash
# 启动后端
cd backend
uvicorn app.main:app --reload --port 8001

# 启动前端（新终端）
cd apps/rowboat
npm run dev
```

### Playwright未安装

```bash
cd apps/rowboat
npm install -D @playwright/test playwright
npx playwright install chromium
```

## 持续测试

### 开发时

- 每次修改后运行相关测试
- 使用 `./scripts/quick_test.sh` 快速验证

### 提交前

- 运行 `./scripts/comprehensive_test_and_fix.sh`
- 确保所有测试通过

### 发布前

- 运行完整测试套件
- 运行Playwright端到端测试
- 手动测试关键功能

## 参考文档

- [测试计划](./docs/TESTING_PLAN.md)
- [测试指南](./docs/COMPREHENSIVE_TESTING_GUIDE.md)
- [测试执行总结](./docs/TEST_EXECUTION_SUMMARY.md)
- [遗留代码清理](./docs/LEGACY_CODE_CLEANUP.md)
- [完成总结](./docs/COMPLETION_SUMMARY.md)

## 支持

如有问题，请查看：
- 测试日志文件
- 测试报告
- 相关文档





