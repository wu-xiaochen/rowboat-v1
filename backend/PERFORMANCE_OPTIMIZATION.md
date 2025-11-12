# 性能优化文档
# Performance Optimization Documentation

本文档记录了已实施的性能优化措施和最佳实践。

This document records the performance optimization measures and best practices that have been implemented.

## 1. 数据库优化 (Database Optimization)

### 1.1 MongoDB索引优化

已为以下集合创建了索引以优化查询性能：

#### Projects 集合索引
- `id` (唯一索引) - 用于快速查找项目
- `createdByUserId` - 用于查询用户的项目
- `createdAt` - 用于排序
- `(createdByUserId, createdAt)` - 复合索引，用于按用户查询并排序

#### Conversations 集合索引
- `id` (唯一索引) - 用于快速查找对话
- `projectId` - 用于查询项目的对话
- `createdAt` - 用于排序
- `(projectId, createdAt)` - 复合索引，用于按项目查询并排序

#### API Keys 集合索引
- `id` (唯一索引) - 用于快速查找API Key
- `projectId` - 用于查询项目的API Keys
- `key` (唯一索引) - 用于API Key验证
- `(key, isActive)` - 复合索引，用于API Key验证查询
- `createdAt` - 用于排序

### 1.2 连接池优化

#### MongoDB连接池配置
```python
maxPoolSize=50      # 最大连接池大小
minPoolSize=10      # 最小连接池大小
maxIdleTimeMS=45000 # 最大空闲时间（45秒）
serverSelectionTimeoutMS=5000  # 服务器选择超时（5秒）
```

#### Redis连接池配置
```python
max_connections=50        # 最大连接数
socket_connect_timeout=5   # 连接超时（5秒）
socket_timeout=5          # Socket超时（5秒）
retry_on_timeout=True     # 超时重试
```

### 1.3 查询优化

- 使用索引字段进行查询
- 使用复合索引优化多字段查询
- 使用`limit`和`skip`进行分页，避免一次性加载大量数据

## 2. 缓存优化 (Cache Optimization)

### 2.1 Redis缓存层

实现了统一的缓存服务 (`app/core/cache.py`)，提供以下功能：

- **缓存读取**：从Redis获取缓存数据
- **缓存写入**：将数据存入Redis，支持TTL设置
- **缓存删除**：删除单个或批量缓存
- **自动序列化**：支持JSON序列化/反序列化

### 2.2 缓存策略

#### 项目缓存
- **缓存键格式**：`project:{project_id}`
- **TTL**：5分钟
- **缓存时机**：
  - 创建项目后立即缓存
  - 查询项目时，先查缓存，未命中再查数据库
  - 更新/删除项目时清除缓存

#### API Key缓存
- **缓存键格式**：`api_key:{key_hash}`
- **TTL**：10分钟（验证频率高）
- **缓存时机**：
  - API Key验证时缓存结果
  - 更新最后使用时间时清除缓存

### 2.3 缓存失效策略

- **写时失效**：更新或删除数据时，自动清除相关缓存
- **TTL过期**：缓存自动过期，确保数据一致性
- **错误容错**：缓存失败不应影响主流程

## 3. API响应优化 (API Response Optimization)

### 3.1 流式响应

聊天端点支持流式响应（SSE），可以：
- 减少用户等待时间
- 提供实时反馈
- 降低服务器内存占用

### 3.2 分页支持

列表查询端点支持分页：
- `skip`：跳过的记录数
- `limit`：返回的最大记录数（默认100，最大1000）

## 4. 代码优化 (Code Optimization)

### 4.1 异步操作

- 所有数据库操作使用异步方法
- 使用`async/await`避免阻塞
- 使用连接池复用连接

### 4.2 错误处理

- 缓存操作失败不应影响主流程
- 使用try-except捕获异常
- 提供降级方案

## 5. 性能监控建议 (Performance Monitoring Recommendations)

### 5.1 监控指标

建议监控以下指标：
- API响应时间
- 数据库查询时间
- 缓存命中率
- 连接池使用率
- 错误率

### 5.2 性能测试

定期进行性能测试：
- 负载测试
- 压力测试
- 并发测试

## 6. 未来优化方向 (Future Optimization Directions)

### 6.1 数据库优化
- [ ] 考虑使用数据库分片（如果数据量很大）
- [ ] 优化大文档查询（workflow字段）
- [ ] 考虑使用只读副本

### 6.2 缓存优化
- [ ] 实现更细粒度的缓存策略
- [ ] 考虑使用缓存预热
- [ ] 实现缓存统计和监控

### 6.3 API优化
- [ ] 实现请求限流（Rate Limiting）
- [ ] 实现响应压缩
- [ ] 优化大文件传输

### 6.4 前端优化
- [ ] 实现前端缓存
- [ ] 优化资源加载
- [ ] 实现懒加载

## 7. 索引创建脚本

使用以下脚本创建索引：

```bash
cd backend
python scripts/create_indexes.py
```

或者在应用启动时自动创建：

```python
from app.core.database import create_mongodb_indexes
await create_mongodb_indexes()
```

---

**文档版本**：v1.0  
**创建日期**：2025-01-27  
**最后更新**：2025-01-27

