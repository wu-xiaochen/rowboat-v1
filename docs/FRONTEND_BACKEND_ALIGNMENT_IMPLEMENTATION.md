# 前后端对齐实施文档
# Frontend-Backend Alignment Implementation Document

## 📋 实施策略

### 原则
1. **保持向后兼容**：修改函数签名时添加可选参数，不破坏现有调用
2. **渐进式迁移**：先更新有projectId的调用，再处理其他情况
3. **错误处理**：统一错误处理格式，确保与原项目一致
4. **响应格式转换**：从`{ success, data, message }`提取`data`

## 🔧 数据源Actions更新

### 1. `listDataSources(projectId: string)`
- ✅ 有projectId，可以直接使用后端API
- 响应格式：`{ success: true, data: DataSource[] }` → 提取`data`

### 2. `getDataSource(sourceId: string, projectId?: string)`
- ⚠️ 原函数只接受sourceId，需要添加可选projectId参数
- 如果有projectId：使用后端API
- 如果没有projectId：使用旧实现（向后兼容）

### 3. `createDataSource({ projectId, ... })`
- ✅ 有projectId，可以直接使用后端API
- 响应格式：`{ success: true, data: DataSource }` → 提取`data`

### 4. `updateDataSource({ sourceId, description })`
- ⚠️ 需要projectId，但原函数没有
- 方案：先通过旧实现获取projectId，然后使用后端API
- 或者：修改函数签名添加projectId参数

### 5. `deleteDataSource(sourceId: string)`
- ⚠️ 需要projectId，但原函数没有
- 方案：先通过旧实现获取projectId，然后使用后端API

### 6. `toggleDataSource(sourceId: string, active: boolean)`
- ⚠️ 需要projectId，但原函数没有
- 方案：先通过旧实现获取projectId，然后使用后端API

## 🔧 对话Actions更新

### 1. `listConversations({ projectId, cursor?, limit? })`
- ✅ 有projectId，可以直接使用后端API
- 响应格式：`{ success: true, data: { items, nextCursor } }` → 提取`data`

### 2. `fetchConversation({ conversationId })`
- ⚠️ 需要projectId，但原函数没有
- 方案：先通过旧实现获取projectId，然后使用后端API

## 🔧 任务Actions更新

### 1. `listJobs({ projectId, filters?, cursor?, limit? })`
- ✅ 有projectId，可以直接使用后端API
- 响应格式：`{ success: true, data: { items, nextCursor } }` → 提取`data`

### 2. `fetchJob({ jobId })`
- ⚠️ 需要projectId，但原函数没有
- 方案：先通过旧实现获取projectId，然后使用后端API

## 📝 实施步骤

### 阶段1：更新有projectId的函数（直接迁移）
1. ✅ `listDataSources` - 有projectId
2. ✅ `createDataSource` - 有projectId
3. ✅ `listConversations` - 有projectId
4. ✅ `listJobs` - 有projectId

### 阶段2：更新需要projectId的函数（添加参数或fallback）
1. ⏳ `getDataSource` - 添加可选projectId参数
2. ⏳ `updateDataSource` - 添加projectId参数或使用fallback
3. ⏳ `deleteDataSource` - 添加projectId参数或使用fallback
4. ⏳ `toggleDataSource` - 添加projectId参数或使用fallback
5. ⏳ `fetchConversation` - 添加projectId参数或使用fallback
6. ⏳ `fetchJob` - 添加projectId参数或使用fallback

### 阶段3：更新前端调用（传递projectId）
1. 更新所有调用`getDataSource`的地方，传递projectId
2. 更新所有调用`updateDataSource`的地方，传递projectId
3. 更新所有调用`deleteDataSource`的地方，传递projectId
4. 更新所有调用`toggleDataSource`的地方，传递projectId
5. 更新所有调用`fetchConversation`的地方，传递projectId
6. 更新所有调用`fetchJob`的地方，传递projectId

### 阶段4：测试和验证
1. 单元测试
2. 集成测试
3. 端到端测试
4. 一致性验证

---

**状态**: ⏳ 进行中

