# Copilot 工具调用功能测试指南

## 快速开始

### 1. 启动服务

#### 后端服务
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

#### 前端服务
```bash
cd apps/rowboat
npm run dev
```

### 2. 验证服务状态

```bash
# 检查后端
curl http://localhost:8001/api/v1/health

# 检查前端
curl http://localhost:3001
```

### 3. 开始测试

#### 选项A：前端界面测试（推荐）

1. **打开浏览器**：访问 http://localhost:3001
2. **导航到 Copilot**：选择项目 → Copilot 标签
3. **执行测试用例**：按照 `docs/COPILOT_TOOL_CALL_TEST_PLAN.md` 执行

#### 选项B：命令行API测试

```bash
# 运行测试脚本
./scripts/test_copilot_api.sh
```

## 测试用例快速参考

### 测试1：简单对话
- **消息**："你好，请介绍一下你自己"
- **预期**：正常文本回复，无工具调用

### 测试2：单轮工具调用
- **消息**："搜索邮件发送相关的工具"
- **预期**：触发 `search_relevant_tools` 工具调用

### 测试3：多轮工具调用
- **消息**："搜索邮件发送工具，然后搜索日历管理工具"
- **预期**：多轮工具调用，每轮正确执行

## 问题排查

### 后端返回内部错误

1. **查看后端控制台**：检查 uvicorn 输出
2. **查看日志文件**：
   ```bash
   tail -f /tmp/backend_copilot.log
   ```
3. **检查请求格式**：确保请求体符合 API 规范

### 前端错误

1. **查看浏览器控制台**：F12 → Console
2. **查看网络请求**：F12 → Network → 检查请求/响应
3. **检查 React 错误**：确保错误信息是字符串

### 工具调用不工作

1. **检查 Composio 配置**：
   - 环境变量 `USE_COMPOSIO_TOOLS=true`
   - Composio API Key 配置正确
2. **查看后端日志**：检查工具调用相关日志
3. **验证消息顺序**：确保 AIMessage → ToolMessage 顺序正确

## 测试检查清单

### 功能检查
- [ ] 简单对话正常
- [ ] 工具调用正常
- [ ] 多轮迭代正常
- [ ] 错误处理正确
- [ ] 消息顺序正确

### 代码质量检查
- [ ] 无 React 渲染错误
- [ ] 无控制台错误
- [ ] 无网络错误
- [ ] 日志清晰

## 记录测试结果

在 `docs/COPILOT_TEST_RESULTS.md` 中记录：
- 测试用例状态
- 发现的问题
- 修复建议

## 下一步

完成测试后：
1. 记录所有测试结果
2. 修复发现的问题
3. 重新测试修复后的功能
4. 更新测试文档

