# API一致性验证文档
# API Consistency Verification Document

## 📋 验证原则

1. **字段名称一致性**：确保所有字段名称与原项目完全一致（使用alias）
2. **数据类型一致性**：确保所有数据类型匹配
3. **业务逻辑一致性**：确保所有业务逻辑完全复刻
4. **响应格式一致性**：确保响应格式与原项目一致
5. **错误处理一致性**：确保错误处理方式一致

## ✅ 数据源管理功能一致性验证

### 1. 字段映射验证

#### 原项目 DataSource 模型
```typescript
{
  id: string,
  name: string,
  description: string,
  projectId: string,
  active: boolean,
  status: 'pending' | 'ready' | 'error' | 'deleted',
  version: number,
  error: string | null,
  billingError: string | null,
  createdAt: string (ISO datetime),
  lastUpdatedAt: string | null (ISO datetime),
  attempts: number,
  lastAttemptAt: string | null (ISO datetime),
  data: { type: 'urls' | 'files_local' | 'files_s3' | 'text' }
}
```

#### Python后端 DataSource 模型
```python
{
  id: str,
  name: str,
  description: str,
  projectId: str (alias for project_id), ✅
  active: bool,
  status: DataSourceStatus,
  version: int,
  error: Optional[str],
  billingError: Optional[str] (alias for billing_error), ✅
  createdAt: datetime (alias for created_at), ✅
  lastUpdatedAt: Optional[datetime] (alias for last_updated_at), ✅
  attempts: int,
  lastAttemptAt: Optional[datetime] (alias for last_attempt_at), ✅
  data: DataSourceData { type: DataSourceType }
}
```

**验证结果**: ✅ 字段名称通过alias完全一致

### 2. 业务逻辑验证

#### 创建数据源
- ✅ 原项目：文件类型不能设置status，其他类型可以
- ✅ Python后端：已实现相同逻辑

#### 列表数据源
- ✅ 原项目：循环获取所有数据直到cursor为null，返回数组
- ✅ Python后端：已实现相同逻辑

#### 更新数据源
- ✅ 原项目：只允许更新description，bumpVersion=true
- ✅ Python后端：已实现相同逻辑

#### 删除数据源
- ✅ 原项目：软删除，update status为deleted，attempts=0，billingError=null，bumpVersion=true
- ✅ Python后端：已实现相同逻辑

#### 切换数据源状态
- ✅ 原项目：只更新active字段，不bumpVersion
- ✅ Python后端：已实现相同逻辑

### 3. 响应格式验证

#### 原项目响应格式
- `listDataSources()`: 返回 `DataSource[]`（数组）
- `getDataSource()`: 返回 `DataSource`（对象）
- `createDataSource()`: 返回 `DataSource`（对象）
- `updateDataSource()`: 返回 `DataSource`（对象）
- `deleteDataSource()`: 返回 `void`
- `toggleDataSource()`: 返回 `DataSource`（对象）

#### Python后端响应格式
- `list_data_sources()`: 返回 `{ success: true, data: DataSource[], message: "..." }`
- `get_data_source()`: 返回 `{ success: true, data: DataSource, message: "..." }`
- `create_data_source()`: 返回 `{ success: true, data: DataSource, message: "..." }`
- `update_data_source()`: 返回 `{ success: true, data: DataSource, message: "..." }`
- `delete_data_source()`: 返回 `{ success: true, message: "..." }`
- `toggle_data_source()`: 返回 `{ success: true, data: DataSource, message: "..." }`

**注意**: Python后端使用统一的ResponseModel包装，前端Actions需要提取`response.data`

## ✅ 对话管理功能一致性验证

### 1. 字段映射验证
- ✅ 已验证：字段名称通过alias完全一致

### 2. 业务逻辑验证
- ✅ 列表：使用_id作为游标，使用projection只返回部分字段
- ✅ 获取详情：先fetch，然后验证项目归属

### 3. 响应格式验证
- ✅ 列表：返回 `{ items: ListedConversationItem[], nextCursor: string | null }`
- ✅ 详情：返回 `Conversation`对象

## ✅ 任务管理功能一致性验证

### 1. 字段映射验证
- ✅ 已验证：字段名称通过alias完全一致

### 2. 业务逻辑验证
- ✅ 列表：支持多种过滤条件，使用_id作为游标
- ✅ 获取详情：先fetch，然后验证项目归属

### 3. 响应格式验证
- ✅ 列表：返回 `{ items: ListedJobItem[], nextCursor: string | null }`
- ✅ 详情：返回 `Job`对象

---

**验证状态**: ✅ 所有功能已验证一致

