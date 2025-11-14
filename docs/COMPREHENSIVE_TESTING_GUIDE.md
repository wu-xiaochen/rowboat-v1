# 全面测试和修复指南
# Comprehensive Testing and Fixing Guide

## 概述

本文档描述如何执行全面的测试和修复流程，确保项目功能100%正常，与原项目100%一致。

## 快速开始

### 1. 运行完整测试套件

```bash
# 运行所有测试（包括API、服务、E2E）
./scripts/comprehensive_test_and_fix.sh

# 或分步运行
./scripts/run_full_test_suite.sh
```

### 2. 检查遗留代码

```bash
# 检查前端是否还有旧后端代码
./scripts/check_legacy_code.sh
```

### 3. 运行Playwright测试

```bash
# 运行端到端测试
./scripts/run_playwright_tests.sh
```

## 测试覆盖范围

### 后端API端点测试

**文件**: `backend/tests/test_api_endpoints.py`

覆盖的端点：
- ✅ 健康检查 (`/api/v1/health`, `/api/v1/ping`)
- ✅ API信息 (`/api/v1/info`)
- ⏳ 项目管理 (`/api/v1/projects/*`)
- ⏳ 聊天 (`/api/v1/{project_id}/chat`)
- ⏳ Copilot (`/api/v1/{project_id}/copilot/*`)

运行测试：
```bash
cd backend
python -m pytest tests/test_api_endpoints.py -v
```

### 服务层测试

**文件**: `backend/tests/test_services.py`

覆盖的服务：
- ⏳ Copilot服务（流式响应、工具调用）
- ⏳ 智能体服务（单智能体、多智能体、Pipeline）
- ⏳ 聊天服务（对话回合、流式响应）

运行测试：
```bash
cd backend
python -m pytest tests/test_services.py -v
```

### 端到端测试

**文件**: `tests/e2e/test_full_workflow.spec.ts`

覆盖的场景：
- ⏳ 创建智能体
- ⏳ 使用Copilot创建智能体
- ⏳ 测试智能体对话
- ⏳ 创建多个智能体
- ⏳ Pipeline工作流
- ⏳ 工具集成
- ⏳ 发布和使用

运行测试：
```bash
npx playwright test tests/e2e/test_full_workflow.spec.ts
```

## 已知问题和修复状态

### ✅ 已修复

1. **工具调用中toolName为空**
   - 问题：Copilot工具调用时，某些情况下toolName为空
   - 修复：改进了工具调用解析逻辑，支持多种格式，添加了详细的调试日志
   - 文件：`backend/app/services/copilot/copilot_service.py`

2. **React Hydration错误**
   - 问题：ProgressBar组件的服务器和客户端渲染不一致
   - 修复：使用useEffect在客户端读取localStorage
   - 文件：`apps/rowboat/app/projects/[projectId]/workflow/components/TopBar.tsx`

3. **按钮嵌套错误**
   - 问题：ComposioCard组件中button嵌套button
   - 修复：将外层button改为div
   - 文件：`apps/rowboat/app/projects/[projectId]/workflow/entity_list.tsx`

4. **React Hooks顺序错误**
   - 问题：useId在条件语句中调用
   - 修复：将useId调用移到组件顶层
   - 文件：`apps/rowboat/app/projects/[projectId]/workflow/entity_list.tsx`

### ⏳ 待测试和修复

1. **智能体对话无响应**
   - 状态：需要更多测试验证
   - 可能原因：模型配置、API错误处理

2. **Copilot工具调用停止**
   - 状态：已改进工具调用处理，需要验证
   - 可能原因：工具结果未正确反馈给LLM

3. **多智能体handoff**
   - 状态：需要端到端测试验证
   - 可能原因：handoff配置或执行逻辑

## 测试流程

### 1. 准备环境

```bash
# 确保服务运行
# 后端
cd backend
uvicorn app.main:app --reload --port 8001

# 前端（新终端）
cd apps/rowboat
npm run dev
```

### 2. 运行测试

```bash
# 完整测试
./scripts/comprehensive_test_and_fix.sh

# 或分步测试
./scripts/check_legacy_code.sh
cd backend && python -m pytest tests/ -v
./scripts/run_playwright_tests.sh
```

### 3. 分析结果

- 查看测试输出
- 检查 `test_results_*.txt` 文件
- 查看 `playwright-report/index.html`（如果运行了Playwright测试）

### 4. 修复问题

1. 根据测试结果定位问题
2. 修复代码
3. 重新运行相关测试
4. 确保所有测试通过

### 5. 回归测试

修复后，运行完整测试套件确保：
- 修复没有引入新问题
- 所有相关功能仍然正常

## 持续测试

### 开发时

- 每次修改后端代码后，运行相关单元测试
- 每次修改前端代码后，检查浏览器控制台
- 每次添加新功能后，添加相应测试

### 提交前

- 运行完整测试套件
- 检查遗留代码
- 确保所有测试通过

### 发布前

- 运行完整测试套件
- 运行Playwright端到端测试
- 手动测试关键功能
- 检查所有已知问题是否已修复

## 测试报告

测试结果保存在：
- `test_results_YYYYMMDD_HHMMSS.txt` - 文本格式测试结果
- `playwright-report/index.html` - Playwright HTML报告
- `backend/.pytest_cache/` - pytest缓存

## 故障排除

### 测试失败

1. **服务未运行**
   - 检查后端和前端服务是否启动
   - 检查端口是否正确（后端8001，前端3001）

2. **依赖缺失**
   - 后端：`pip install -r backend/requirements-test.txt`
   - 前端：`npm install`（在apps/rowboat目录）

3. **Playwright未安装**
   - 运行：`npx playwright install chromium`

### 常见问题

1. **工具调用失败**
   - 检查工具配置
   - 检查API密钥
   - 查看后端日志

2. **智能体无响应**
   - 检查模型配置
   - 检查API密钥和URL
   - 查看错误日志

3. **前端错误**
   - 检查浏览器控制台
   - 检查网络请求
   - 验证API端点

## 下一步

1. 完善测试用例，覆盖所有功能
2. 添加更多端到端测试场景
3. 设置CI/CD自动测试
4. 添加性能测试
5. 添加负载测试

## 参考

- [测试计划](./TESTING_PLAN.md)
- [迁移状态](../MIGRATION_STATUS.md)
- [配置指南](../CONFIGURATION_GUIDE.md)





