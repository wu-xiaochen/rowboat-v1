# 文档清理计划
# Documentation Cleanup Plan

**创建日期**：2025-01-27

## 文档分类

### ✅ 保留的核心文档

1. **项目规则和计划**
   - `.cursor/rules/project-rules.mdc` - 项目开发规则（核心）
   - `DEVELOPMENT-PLAN.md` - 开发计划
   - `README.md` - 项目主README

2. **后端文档**
   - `backend/README.md` - 后端README
   - `backend/AGENT_FRAMEWORK_ANALYSIS.md` - 智能体框架分析
   - `backend/API_ENDPOINTS_INVENTORY.md` - API端点清单
   - `backend/PERFORMANCE_OPTIMIZATION.md` - 性能优化文档
   - `backend/docs/function_tool_usage.md` - 工具使用指南

3. **优化和迁移文档**
   - `OPTIMIZATION_PLAN.md` - 优化计划
   - `OPTIMIZATION_STATUS.md` - 优化状态
   - `MIGRATION_STATUS.md` - 迁移状态

### ⚠️ 需要整理的文档

1. **E2E测试文档（重复）**
   - `E2E_TEST_PLAN.md` - 测试计划
   - `E2E_TEST_EXECUTION.md` - 测试执行记录
   - `E2E_TEST_FINAL_REPORT.md` - 最终报告
   - `E2E_TEST_SUMMARY.md` - 测试总结
   - `E2E_TEST_COMPLETION_SUMMARY.md` - 完成总结
   - `E2E_TEST_RESULTS.md` - 测试结果
   - `E2E_TESTING_GUIDE.md` - 测试指南

   **建议**：合并为1-2个文档
   - 保留：`E2E_TEST_FINAL_REPORT.md`（最终报告）
   - 保留：`E2E_TESTING_GUIDE.md`（测试指南，如果内容有价值）
   - 删除或归档：其他重复文档

2. **配置文档**
   - `apps/rowboat/COMPOSIO_API_KEY_SETUP.md` - Composio配置说明
   - **建议**：保留（有用的配置指南）

### ❌ 可以删除的文档

1. **过时的文档**
   - `backend/PROJECT_UPDATE_SUMMARY.md` - 项目更新总结（信息已整合到其他文档）
   - `logo.949c267c.svg` - 旧logo文件（如果已有新logo）

2. **重复的测试文档**
   - `E2E_TEST_PLAN.md` - 内容已包含在最终报告中
   - `E2E_TEST_RESULTS.md` - 内容已包含在最终报告中
   - `E2E_TEST_EXECUTION.md` - 详细记录，可以归档或删除
   - `E2E_TEST_SUMMARY.md` - 内容已包含在最终报告中
   - `E2E_TEST_COMPLETION_SUMMARY.md` - 内容已包含在最终报告中

## 清理建议

### 立即操作
1. 合并E2E测试文档为1-2个核心文档
2. 删除过时的更新总结文档
3. 整理文档到合适的目录

### 后续操作
1. 创建文档索引
2. 更新README，添加文档链接
3. 建立文档维护规范

---

**执行状态**：待执行

