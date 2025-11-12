# 端到端测试指南
# End-to-End Testing Guide

本文档说明如何使用Playwright MCP进行端到端测试。

This document explains how to use Playwright MCP for end-to-end testing.

## 前置条件

1. **环境准备**
   - MongoDB运行在 localhost:27017
   - Redis运行在 localhost:6379
   - Qdrant运行在 localhost:6333（如果启用RAG）

2. **配置检查**
   - 后端`.env`文件配置正确
   - 前端`.env.local`文件配置正确

## 启动服务

### 方法1：使用启动脚本

```bash
cd /Users/xiaochenwu/Desktop/rowboat
./scripts/start_services.sh
```

### 方法2：手动启动

**启动后端**：
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**启动前端**：
```bash
cd apps/rowboat
npm run dev
```

### 验证服务运行

**检查后端**：
```bash
curl http://localhost:8001/api/v1/health
```

**检查前端**：
```bash
curl http://localhost:3001
```

## 执行端到端测试

由于需要使用Playwright MCP工具，测试将通过AI助手使用浏览器MCP工具执行。

### 测试流程

1. **基础功能测试**
   - 应用启动和导航
   - 品牌显示验证
   - 页面加载验证

2. **项目管理测试**
   - 创建项目
   - 查看项目列表
   - 编辑项目
   - 删除项目

3. **工作流编辑器测试**
   - 创建智能体
   - 创建工具
   - 创建提示词
   - 创建管道
   - 管理数据源

4. **聊天功能测试**
   - Playground聊天
   - 流式响应
   - 工具调用
   - 多智能体协作

5. **Copilot功能测试**
   - Copilot对话
   - 智能体创建

6. **API密钥管理测试**
   - 创建API密钥
   - 查看API密钥列表
   - 删除API密钥

7. **对话和任务管理测试**
   - 查看对话列表
   - 查看对话详情
   - 查看任务列表
   - 查看任务详情

8. **触发器管理测试**
   - 外部触发器
   - 一次性触发器
   - 重复触发器

9. **项目设置测试**
   - 项目配置
   - Composio工具包

10. **中文本地化测试**
    - 界面文本验证
    - 错误消息验证

11. **错误处理和边界情况测试**
    - 网络错误处理
    - 无效输入验证
    - 空状态显示

## 测试执行

测试将通过AI助手使用浏览器MCP工具逐步执行。每个测试步骤将：

1. 导航到相应页面
2. 执行操作（点击、输入等）
3. 验证结果
4. 截图保存
5. 记录测试结果

## 测试结果

测试结果将记录在：
- `E2E_TEST_RESULTS.md` - 详细测试结果
- `E2E_TEST_RESULTS.json` - 机器可读的测试结果

## 问题报告

发现的问题将按严重程度分类：
- **P0 - 严重**：阻塞核心功能
- **P1 - 重要**：影响主要功能
- **P2 - 一般**：影响次要功能
- **P3 - 优化**：体验优化建议

---

**文档版本**：v1.0  
**创建日期**：2025-01-27  
**最后更新**：2025-01-27

