# API端点实现计划
# API Endpoints Implementation Plan

## 📋 实现原则

1. **确认缺失功能**：只实现确实缺失且合理可行的功能
2. **前后端对齐**：确保API设计与前端需求一致，禁用前端旧实现
3. **详细规划**：每个功能都有详细设计和测试计划
4. **不影响现有功能**：新功能与现有功能协同工作
5. **严格规范**：遵循项目开发规范

## 🎯 实现优先级

### 阶段一：高优先级核心功能（立即实现）

#### 1. 项目管理增强功能 ✅
- [x] 旋转项目Secret (`POST /api/v1/projects/{project_id}/rotate-secret`)
- [x] 更新项目名称 (`PUT /api/v1/projects/{project_id}/name`)
- [x] 保存草稿工作流 (`PUT /api/v1/projects/{project_id}/draft-workflow`)
- [x] 发布工作流 (`PUT /api/v1/projects/{project_id}/live-workflow`)
- [x] 回滚到生产工作流 (`POST /api/v1/projects/{project_id}/revert-to-live`)

#### 2. 数据源（RAG）管理功能 ✅
- [x] 创建数据源 (`POST /api/v1/{project_id}/data-sources`)
- [x] 获取数据源列表 (`GET /api/v1/{project_id}/data-sources`)
- [x] 获取数据源详情 (`GET /api/v1/{project_id}/data-sources/{source_id}`)
- [x] 更新数据源 (`PUT /api/v1/{project_id}/data-sources/{source_id}`)
- [x] 删除数据源 (`DELETE /api/v1/{project_id}/data-sources/{source_id}`)
- [x] 切换数据源状态 (`POST /api/v1/{project_id}/data-sources/{source_id}/toggle`)

#### 3. 对话管理功能 ✅
- [x] 获取对话列表 (`GET /api/v1/{project_id}/conversations`)
- [x] 获取对话详情 (`GET /api/v1/{project_id}/conversations/{conversation_id}`)

#### 4. 任务管理功能 ✅
- [x] 获取任务列表 (`GET /api/v1/{project_id}/jobs`)
- [x] 获取任务详情 (`GET /api/v1/{project_id}/jobs/{job_id}`)

### 阶段二：中优先级功能（后续实现）

#### 5. 数据源文档管理
- [ ] 添加文档到数据源 (`POST /api/v1/{project_id}/data-sources/{source_id}/docs`)
- [ ] 列出数据源文档 (`GET /api/v1/{project_id}/data-sources/{source_id}/docs`)
- [ ] 删除数据源文档 (`DELETE /api/v1/{project_id}/data-sources/{source_id}/docs/{doc_id}`)

#### 6. 文件上传/下载
- [ ] 获取文件上传URL (`POST /api/v1/{project_id}/data-sources/{source_id}/upload-urls`)
- [ ] 获取文件下载URL (`GET /api/v1/{project_id}/data-sources/{source_id}/files/{file_id}/download-url`)

#### 7. MCP服务器管理
- [ ] 添加MCP服务器 (`POST /api/v1/{project_id}/mcp-servers`)
- [ ] 删除MCP服务器 (`DELETE /api/v1/{project_id}/mcp-servers/{server_name}`)
- [ ] 获取MCP服务器工具 (`POST /api/v1/{project_id}/mcp-servers/{server_name}/fetch-tools`)

### 阶段三：低优先级功能（可选实现）

#### 8. Composio集成
#### 9. 定时任务和循环任务
#### 10. 其他辅助功能

---

## 📝 实现步骤

### 步骤1：创建数据模型
- 定义DataSource模型
- 定义DataSourceDoc模型
- 定义Job模型
- 更新现有模型（如Project添加webhookUrl字段）

### 步骤2：创建Repository层
- DataSourcesRepository
- DataSourceDocsRepository
- JobsRepository

### 步骤3：创建Service层
- DataSourcesService
- JobsService

### 步骤4：创建API端点
- 按模块创建端点文件
- 实现路由处理函数
- 添加请求/响应模型

### 步骤5：编写测试
- 单元测试
- 集成测试
- API端点测试

### 步骤6：前后端对齐 ✅
- [x] 创建后端API客户端 (`backend-api-client.ts`)
- [x] 更新前端Actions使用后端API
  - [x] 更新`data-source.actions.ts` ✅
  - [x] 更新`conversation.actions.ts` ✅
  - [x] 更新`job.actions.ts` ✅
- [x] 禁用前端旧实现（标记为已弃用）✅
- [x] 更新前端组件传递projectId ✅
- [x] 测试前后端集成 ✅

---

## 🔍 详细设计

### 1. 项目管理增强功能

#### 1.1 旋转项目Secret
**端点**: `POST /api/v1/projects/{project_id}/rotate-secret`

**请求**: 无请求体

**响应**:
```json
{
  "success": true,
  "data": {
    "secret": "new_secret_value"
  },
  "message": "Secret已成功旋转"
}
```

**实现**:
- 生成新的secret
- 更新项目记录
- 返回新secret（仅此一次）

#### 1.2 更新项目名称
**端点**: `PUT /api/v1/projects/{project_id}/name`

**请求**:
```json
{
  "name": "新项目名称"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "id": "project_id",
    "name": "新项目名称"
  },
  "message": "项目名称已更新"
}
```

#### 1.3 保存草稿工作流
**端点**: `PUT /api/v1/projects/{project_id}/draft-workflow`

**请求**:
```json
{
  "workflow": {
    "agents": [...],
    "tools": [...],
    "prompts": [...],
    "pipelines": [...],
    "startAgent": "agent_name"
  }
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "id": "project_id",
    "draftWorkflow": {...}
  },
  "message": "草稿工作流已保存"
}
```

#### 1.4 发布工作流
**端点**: `PUT /api/v1/projects/{project_id}/live-workflow`

**请求**: 无请求体（使用当前draftWorkflow）

**响应**:
```json
{
  "success": true,
  "data": {
    "id": "project_id",
    "liveWorkflow": {...}
  },
  "message": "工作流已发布"
}
```

#### 1.5 回滚到生产工作流
**端点**: `POST /api/v1/projects/{project_id}/revert-to-live`

**请求**: 无请求体

**响应**:
```json
{
  "success": true,
  "data": {
    "id": "project_id",
    "draftWorkflow": {...}  // 回滚后的draftWorkflow = liveWorkflow
  },
  "message": "已回滚到生产工作流"
}
```

### 2. 数据源管理功能

#### 2.1 数据源模型
```python
class DataSourceType(str, Enum):
    FILES = "files"
    WEB = "web"
    TEXT = "text"

class DataSource(BaseModel):
    id: str
    project_id: str
    name: str
    type: DataSourceType
    active: bool
    config: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]
```

#### 2.2 创建数据源
**端点**: `POST /api/v1/{project_id}/data-sources`

**请求**:
```json
{
  "name": "数据源名称",
  "type": "files|web|text",
  "config": {
    // 根据type不同而不同
  }
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "id": "source_id",
    "name": "数据源名称",
    "type": "files",
    "active": true,
    ...
  },
  "message": "数据源已创建"
}
```

#### 2.3 其他数据源端点
- 列表、详情、删除、切换状态等标准CRUD操作

### 3. 对话管理功能

#### 3.1 对话模型
```python
class Conversation(BaseModel):
    id: str
    project_id: str
    created_at: datetime
    updated_at: Optional[datetime]
    # 其他字段...
```

#### 3.2 获取对话列表
**端点**: `GET /api/v1/{project_id}/conversations`

**查询参数**:
- `limit`: 每页数量（默认20）
- `cursor`: 分页游标

**响应**:
```json
{
  "success": true,
  "data": {
    "items": [...],
    "nextCursor": "cursor_string"
  },
  "message": "对话列表获取成功"
}
```

### 4. 任务管理功能

#### 4.1 任务模型
```python
class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Job(BaseModel):
    id: str
    project_id: str
    status: JobStatus
    created_at: datetime
    completed_at: Optional[datetime]
    # 其他字段...
```

#### 4.2 获取任务列表
**端点**: `GET /api/v1/{project_id}/jobs`

**查询参数**:
- `status`: 过滤状态
- `limit`: 每页数量
- `cursor`: 分页游标

---

## 🧪 测试计划

### 单元测试
- Repository层测试
- Service层测试
- 模型验证测试

### 集成测试
- API端点测试
- 数据库操作测试
- 服务集成测试

### 端到端测试
- 完整流程测试
- 前后端集成测试

---

## 📊 进度跟踪

### 阶段一进度
- [ ] 项目管理增强功能（5个端点）
- [ ] 数据源管理功能（5个端点）
- [ ] 对话管理功能（2个端点）
- [ ] 任务管理功能（2个端点）

**总计**: 14个高优先级端点

---

**最后更新**: 2025-01-27  
**状态**: 计划制定完成，准备开始实现

