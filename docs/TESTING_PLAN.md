# 完整测试计划
# Complete Testing Plan

## 测试目标

1. **100%功能覆盖**: 确保所有原项目功能在新后端中完整实现
2. **API端点完整性**: 验证所有后端API端点正常工作
3. **前端迁移完整性**: 确保前端完全使用新后端，无残留旧代码
4. **端到端测试**: 使用Playwright测试所有用户交互流程
5. **回归测试**: 修复所有发现的bug并确保不再出现

## 测试范围

### 1. 后端API端点测试

#### 健康检查端点
- [x] GET `/api/v1/health` - 健康检查
- [x] GET `/api/v1/ping` - Ping测试

#### 信息端点
- [x] GET `/api/v1/info` - API信息

#### 项目端点
- [ ] POST `/api/v1/projects` - 创建项目
- [ ] GET `/api/v1/projects` - 列出项目
- [ ] GET `/api/v1/projects/{project_id}` - 获取项目
- [ ] PUT `/api/v1/projects/{project_id}` - 更新项目
- [ ] DELETE `/api/v1/projects/{project_id}` - 删除项目

#### 聊天端点
- [ ] POST `/api/v1/{project_id}/chat` (stream=true) - 流式聊天
- [ ] POST `/api/v1/{project_id}/chat` (stream=false) - 非流式聊天

#### Copilot端点
- [ ] POST `/api/v1/{project_id}/copilot/stream` - Copilot流式响应
- [ ] POST `/api/v1/{project_id}/copilot/edit-agent-instructions` - 编辑智能体提示词

#### API密钥端点
- [ ] POST `/api/v1/{project_id}/api-keys` - 创建API密钥
- [ ] GET `/api/v1/{project_id}/api-keys` - 列出API密钥
- [ ] DELETE `/api/v1/{project_id}/api-keys/{key_id}` - 删除API密钥

### 2. 服务层测试

#### Copilot服务
- [ ] 基本流式响应
- [ ] 带工具的流式响应
- [ ] 工具调用处理
- [ ] 错误处理（503, 模型不存在等）
- [ ] 编辑智能体提示词

#### 智能体服务
- [ ] 单智能体流式响应
- [ ] 多智能体handoff
- [ ] Pipeline执行
- [ ] 工具调用
- [ ] 错误处理

#### 聊天服务
- [ ] 基本对话回合
- [ ] 流式响应
- [ ] 对话历史管理
- [ ] 错误处理

### 3. 前端功能测试

#### 项目管理
- [ ] 创建项目
- [ ] 编辑项目名称
- [ ] 删除项目
- [ ] 项目列表

#### 智能体管理
- [ ] 创建智能体
- [ ] 编辑智能体配置
- [ ] 删除智能体
- [ ] 设置起始智能体
- [ ] 启用/禁用智能体

#### Copilot功能
- [ ] 使用Copilot创建智能体
- [ ] 使用Copilot添加工具
- [ ] 使用Copilot编辑智能体提示词
- [ ] Copilot工具调用
- [ ] Copilot错误处理

#### 聊天功能
- [ ] 发送消息
- [ ] 接收流式响应
- [ ] 消息历史
- [ ] 错误处理

#### Pipeline功能
- [ ] 创建Pipeline
- [ ] 添加智能体到Pipeline
- [ ] Pipeline执行

#### 工具管理
- [ ] 添加工具
- [ ] 编辑工具
- [ ] 删除工具
- [ ] Composio工具集成

### 4. 端到端测试场景

#### 场景1: 创建智能客服
1. 打开项目
2. 使用Copilot创建智能客服
3. 验证智能体已创建
4. 测试智能体对话
5. 验证响应正常

#### 场景2: 多智能体工作流
1. 创建多个智能体
2. 配置智能体handoff
3. 测试多智能体对话
4. 验证handoff正常工作

#### 场景3: Pipeline工作流
1. 创建Pipeline
2. 添加多个步骤智能体
3. 执行Pipeline
4. 验证所有步骤执行

#### 场景4: 工具集成
1. 添加Composio工具
2. 配置工具认证
3. 在智能体中使用工具
4. 验证工具调用

#### 场景5: 发布和使用
1. 创建并配置智能体
2. 发布项目
3. 使用"使用助手"功能
4. 验证API配置

## 测试执行

### 运行所有测试

```bash
# 运行完整测试套件
./scripts/run_full_test_suite.sh

# 只运行后端测试
cd backend && python -m pytest tests/ -v

# 只运行Playwright测试
npx playwright test

# 检查遗留代码
./scripts/check_legacy_code.sh
```

### 持续测试流程

1. **修复当前问题** → 运行测试 → 验证修复
2. **添加新功能** → 编写测试 → 运行测试 → 验证功能
3. **重构代码** → 运行测试 → 确保无回归
4. **发布前** → 运行完整测试套件 → 修复所有失败

## 已知问题跟踪

### 当前问题
1. ✅ 工具调用中toolName为空 - 已修复
2. ✅ Hydration错误 - 已修复
3. ✅ 按钮嵌套错误 - 已修复
4. ⏳ 智能体对话无响应 - 需要进一步测试

### 修复状态
- [x] 工具调用参数处理
- [x] 错误处理改进
- [x] 前端hydration问题
- [ ] 智能体响应问题（需要更多测试）

## 测试报告

测试结果将保存在：
- `backend/tests/reports/` - 后端测试报告
- `playwright-report/` - Playwright测试报告
- `test-results/` - 测试结果详情





