# 前端更新剩余任务
# Frontend Update Remaining Tasks

## ✅ 已完成的更新

### Actions更新
- ✅ `listDataSources` - 已迁移到后端API
- ✅ `createDataSource` - 已迁移到后端API
- ✅ `getDataSource` - 已添加可选projectId参数，支持后端API
- ✅ `updateDataSource` - 已添加可选projectId参数，支持后端API
- ✅ `deleteDataSource` - 已添加可选projectId参数，支持后端API
- ✅ `toggleDataSource` - 已添加可选projectId参数，支持后端API
- ✅ `listConversations` - 已迁移到后端API
- ✅ `fetchConversation` - 已添加可选projectId参数，支持后端API
- ✅ `listJobs` - 已迁移到后端API
- ✅ `fetchJob` - 已添加可选projectId参数，支持后端API

### 前端组件更新
- ✅ `source-page.tsx` - 已更新所有`getDataSource`调用传递projectId
- ✅ `source-page.tsx` - 已更新`updateDataSource`调用传递projectId

## ⏳ 需要更新的前端组件调用

### 数据源相关
1. **`apps/rowboat/app/projects/[projectId]/entities/datasource_config.tsx`**
   - 第46行：`getDataSource(dataSourceId)` → `getDataSource(dataSourceId, projectId)`
   - 第93行：`getDataSource(dataSourceId)` → `getDataSource(dataSourceId, projectId)`
   - 第126行：`getDataSource(dataSourceId)` → `getDataSource(dataSourceId, projectId)`
   - 注意：该组件已有`projectId`状态（第35行），从URL提取

2. **`apps/rowboat/app/projects/[projectId]/workflow/components/DataSourcesModal.tsx`**
   - 第36行：`getDataSource(sourceId)` → `getDataSource(sourceId, projectId)`
   - 注意：该组件已有`projectId` prop（第25行）

3. **`apps/rowboat/app/projects/[projectId]/sources/components/self-updating-source-status.tsx`**
   - 第27行：`getDataSource(sourceId)` → `getDataSource(sourceId, projectId)`
   - 注意：该组件需要添加`projectId` prop

4. **`apps/rowboat/app/projects/[projectId]/sources/components/toggle-source.tsx`**
   - 第23行：`toggleDataSource(sourceId, !isActive)` → `toggleDataSource(sourceId, !isActive, projectId)`
   - 注意：该组件需要添加`projectId` prop

5. **`apps/rowboat/app/projects/[projectId]/sources/components/delete.tsx`**
   - 第13行：`deleteDataSource(sourceId)` → `deleteDataSource(sourceId, projectId)`
   - 注意：该组件需要添加`projectId` prop

6. **`apps/rowboat/app/projects/[projectId]/workflow/entity_list.tsx`**
   - 第1215行：`deleteDataSource(dataSource.id)` → `deleteDataSource(dataSource.id, projectId)`
   - 注意：该组件已有`projectId` prop

### 对话相关
1. **`apps/rowboat/app/projects/[projectId]/conversations/components/conversation-view.tsx`**
   - 第86行：`fetchConversation({ conversationId })` → `fetchConversation({ conversationId, projectId })`
   - 注意：该组件已有`projectId` prop（第78行）

### 任务相关
1. **`apps/rowboat/app/projects/[projectId]/jobs/components/job-view.tsx`**
   - 第20行：`fetchJob({ jobId })` → `fetchJob({ jobId, projectId })`
   - 注意：该组件已有`projectId` prop（第12行）

## 📝 更新步骤

### 步骤1：更新组件Props
为需要projectId的组件添加`projectId` prop：
- `SelfUpdatingSourceStatus`
- `ToggleSource`
- `DeleteSource`

### 步骤2：更新函数调用
在所有调用这些Actions的地方传递`projectId`参数。

### 步骤3：测试验证
1. 测试数据源功能
2. 测试对话功能
3. 测试任务功能
4. 端到端测试

---

**状态**: ⏳ 部分完成，需要继续更新前端组件调用

