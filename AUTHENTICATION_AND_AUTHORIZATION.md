# 认证与授权系统说明文档

## 1. 概述

本文档详细说明质信智购项目的认证（Authentication）和授权（Authorization）系统，包括用户类型、权限模型和功能差异。

## 2. 授权验证的作用

### 2.1 什么是授权验证？

授权验证（Authorization）是确保用户或 API 客户端有权限访问特定资源（主要是项目）的安全机制。

### 2.2 授权验证的主要目的

1. **项目访问控制**：
   - 确保只有项目的成员才能访问项目数据
   - 防止未授权用户访问或修改项目

2. **API 访问控制**：
   - 支持通过 API Key 进行程序化访问
   - 验证 API Key 的有效性和权限

3. **资源隔离**：
   - 不同用户的项目数据相互隔离
   - 确保数据安全和隐私

### 2.3 授权验证的两种方式

#### 方式1：用户身份验证（User Authentication）
- **调用者类型**：`caller: "user"`
- **验证方式**：检查用户是否为项目的成员
- **使用场景**：前端 Web 应用的用户操作
- **验证流程**：
  1. 用户通过 Auth0 登录（如果 `USE_AUTH=true`）
  2. 获取用户 ID
  3. 检查用户是否为项目的成员（通过 `ProjectMembersRepository.exists()`）
  4. 如果用户是成员，允许访问；否则拒绝访问

#### 方式2：API Key 验证（API Key Authentication）
- **调用者类型**：`caller: "api"`
- **验证方式**：验证 API Key 的有效性和所属项目
- **使用场景**：后端 API 调用、第三方集成
- **验证流程**：
  1. 从请求头中提取 API Key（`Authorization: Bearer {key}`）
  2. 哈希 API Key 并查询数据库
  3. 检查 API Key 是否有效且属于目标项目
  4. 更新 API Key 的最后使用时间
  5. 如果 API Key 有效，允许访问；否则拒绝访问

### 2.4 授权验证的实现

授权验证通过 `ProjectActionAuthorizationPolicy` 类实现：

```typescript
// apps/rowboat/src/application/policies/project-action-authorization.policy.ts
class ProjectActionAuthorizationPolicy {
    async authorize(data: {
        caller: "user" | "api",
        userId?: string,
        apiKey?: string,
        projectId: string
    }): Promise<void> {
        if (caller === "user") {
            // 检查用户是否为项目成员
            const membership = await this.projectMembersRepository.exists(projectId, userId);
            if (!membership) {
                throw new NotAuthorizedError('User is not a member of the project');
            }
        } else {
            // 验证 API Key
            const result = await this.apiKeysRepository.checkAndConsumeKey(projectId, apiKey);
            if (!result) {
                throw new NotAuthorizedError('Invalid API key');
            }
        }
    }
}
```

## 3. 用户类型

### 3.1 Guest 用户（访客用户）

#### 定义
Guest 用户是在 `USE_AUTH=false` 时使用的默认用户，不需要登录即可访问系统。

#### 特征
- **用户 ID**：`"guest_user"`
- **Auth0 ID**：`"guest_user"`
- **邮箱**：`"wuxiaochen0802@gmail.com"`
- **名称**：`"Guest"`
- **创建时间**：系统启动时定义

#### 使用场景
- 开发和测试环境
- 不需要用户认证的单用户部署
- 演示和预览环境

#### 代码定义
```typescript
// apps/rowboat/app/lib/auth.ts
export const GUEST_DB_USER: z.infer<typeof User> = {
    id: "guest_user",
    auth0Id: "guest_user",
    name: "Guest",
    email: "wuxiaochen0802@gmail.com",
    createdAt: new Date().toISOString(),
}
```

#### Guest 用户的 Billing 信息
```typescript
// apps/rowboat/app/lib/billing.ts
const GUEST_BILLING_CUSTOMER = {
    id: "guest-user",
    userId: "guest-user",
    name: "Guest",
    email: "wuxiaochen0802@gmail.com",
    stripeCustomerId: "guest",
    stripeSubscriptionId: "test",
    subscriptionPlan: "free",
    subscriptionStatus: "active",
    createdAt: new Date().toISOString(),
};
```

### 3.2 普通用户（Authenticated User）

#### 定义
普通用户是通过 Auth0 认证的用户，需要在系统中注册和登录。

#### 特征
- **用户 ID**：MongoDB 中的唯一 ID
- **Auth0 ID**：Auth0 提供的用户标识符
- **邮箱**：用户的电子邮件地址
- **名称**：用户的显示名称
- **Billing Customer ID**：可选，用于计费功能

#### 创建流程
1. 用户通过 Auth0 登录
2. 系统检查用户是否存在于数据库中
3. 如果不存在，自动创建用户记录
4. 如果存在，返回现有用户记录

#### 代码实现
```typescript
// apps/rowboat/app/lib/auth.ts
export async function requireAuth(): Promise<z.infer<typeof User>> {
    if (!USE_AUTH) {
        return GUEST_DB_USER;
    }

    const { user } = await auth0.getSession() || {};
    if (!user) {
        redirect('/auth/login');
    }

    // 获取或创建用户
    const usersRepository = container.resolve<IUsersRepository>("usersRepository");
    let dbUser = await getUserFromSessionId(user.sub);
    
    if (!dbUser) {
        dbUser = await usersRepository.create({
            auth0Id: user.sub,
            email: user.email,
        });
    }

    return dbUser;
}
```

## 4. 项目成员（Project Members）

### 4.1 什么是项目成员？

项目成员是拥有项目访问权限的用户。只有项目成员才能访问和操作项目。

### 4.2 项目成员的创建

当用户创建项目时，系统自动将该用户添加为项目成员：

```typescript
// apps/rowboat/src/application/use-cases/projects/create-project.use-case.ts
async execute(request: z.infer<typeof InputSchema>): Promise<z.infer<typeof Project>> {
    // 创建项目
    const project = await this.projectsRepository.create({
        ...request.data,
        workflow,
        createdByUserId: request.userId,
        name: request.data.name || `Assistant ${count + 1}`,
        secret,
    });

    // 自动创建项目成员关系
    await this.projectMembersRepository.create({
        projectId: project.id,
        userId: request.userId,
    });

    return project;
}
```

### 4.3 项目成员的数据结构

```typescript
// apps/rowboat/src/entities/models/project-member.ts
export const ProjectMember = z.object({
    id: z.string(),
    userId: z.string(),
    projectId: z.string(),
    createdAt: z.string().datetime(),
    lastUpdatedAt: z.string().datetime(),
});
```

### 4.4 项目成员的权限

目前系统中，**所有项目成员拥有相同的权限**：
- 可以访问项目数据
- 可以修改项目配置
- 可以创建和管理项目资源
- 可以删除项目（需要进一步验证）

**注意**：系统中没有实现角色区分（如 owner、admin、member 等），所有成员权限相同。

## 5. API Key

### 5.1 什么是 API Key？

API Key 是用于程序化访问项目的密钥，允许第三方应用或服务通过 API 访问项目。

### 5.2 API Key 的特征

- **所属项目**：每个 API Key 属于一个特定的项目
- **唯一性**：每个 API Key 都是唯一的
- **安全性**：API Key 在数据库中存储为哈希值
- **使用跟踪**：系统记录 API Key 的最后使用时间

### 5.3 API Key 的数据结构

```typescript
// apps/rowboat/src/entities/models/api-key.ts
export const ApiKey = z.object({
    id: z.string(),
    projectId: z.string(),
    key: z.string(),
    createdAt: z.string().datetime(),
    lastUsedAt: z.string().datetime().optional(),
});
```

### 5.4 API Key 的使用

API Key 通过 HTTP 请求头传递：

```
Authorization: Bearer {api_key}
```

后端验证 API Key：

```python
# backend/app/api/dependencies.py
async def verify_api_key(
    authorization: Optional[str] = Header(None)
) -> str:
    # 解析 API Key
    api_key = authorization.split()[1]
    
    # 哈希 API Key
    key_hash = hash_api_key(api_key)
    
    # 查询数据库
    api_key_obj = await repo.get_by_key_hash(key_hash)
    
    if api_key_obj is None:
        raise HTTPException(status_code=401, detail="无效的API Key")
    
    return api_key_obj.project_id
```

## 6. 功能差异

### 6.1 Guest 用户 vs 普通用户

| 功能 | Guest 用户 | 普通用户 |
|------|-----------|---------|
| **登录要求** | 不需要 | 需要（通过 Auth0） |
| **用户识别** | 固定 ID (`guest_user`) | 唯一 ID（MongoDB） |
| **项目创建** | 可以创建 | 可以创建 |
| **项目访问** | 可以访问 | 可以访问（需要是项目成员） |
| **数据持久化** | 数据存储在数据库中 | 数据存储在数据库中 |
| **多用户支持** | 不支持（所有操作使用同一个 Guest 用户） | 支持（每个用户有独立的数据） |
| **Billing 功能** | 使用 Guest Billing Customer | 使用真实的 Billing Customer |
| **使用场景** | 开发、测试、演示 | 生产环境 |

### 6.2 项目成员 vs API Key

| 功能 | 项目成员 | API Key |
|------|---------|---------|
| **访问方式** | 通过用户身份 | 通过 API Key |
| **使用场景** | Web 前端操作 | API 调用、第三方集成 |
| **权限范围** | 可以访问项目所有功能 | 可以访问项目所有功能 |
| **安全性** | 通过 Auth0 认证 | 通过 API Key 验证 |
| **使用跟踪** | 不跟踪 | 跟踪最后使用时间 |
| **创建方式** | 自动创建（创建项目时） | 手动创建（通过 API） |

### 6.3 启用/禁用认证

#### USE_AUTH=false（当前配置）
- 使用 Guest 用户
- 不需要登录
- 所有用户共享同一个 Guest 用户身份
- 适合开发、测试和演示环境

#### USE_AUTH=true
- 使用 Auth0 认证
- 需要用户登录
- 每个用户有独立的身份和数据
- 适合生产环境

## 7. 配置说明

### 7.1 环境变量

```bash
# 启用/禁用认证
USE_AUTH=false  # 当前配置：禁用认证，使用 Guest 用户

# Auth0 配置（当 USE_AUTH=true 时使用）
AUTH0_ISSUER_BASE_URL=your-auth0-domain
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret
AUTH0_BASE_URL=http://localhost:3001
AUTH0_SECRET=your-secret
AUTH0_SCOPE=openid profile email
AUTH0_AUDIENCE=your-audience
```

### 7.2 功能开关

```typescript
// apps/rowboat/app/lib/feature_flags.ts
export const USE_AUTH = process.env.USE_AUTH === 'true';
export const USE_BILLING = process.env.NEXT_PUBLIC_USE_BILLING === 'true' || process.env.USE_BILLING === 'true';
```

## 8. 安全考虑

### 8.1 当前实现的局限性

1. **没有角色区分**：
   - 所有项目成员拥有相同的权限
   - 没有 owner、admin、member 等角色区分

2. **Guest 用户的安全性**：
   - 在 `USE_AUTH=false` 时，所有用户共享同一个 Guest 用户身份
   - 不适合多用户生产环境

3. **API Key 管理**：
   - 没有实现 API Key 的撤销和禁用功能（虽然有 `is_active` 字段）
   - 没有实现 API Key 的权限范围限制

### 8.2 建议的改进

1. **实现角色系统**：
   - 添加 owner、admin、member 等角色
   - 根据角色限制权限

2. **改进 Guest 用户**：
   - 在 `USE_AUTH=false` 时，考虑使用会话 ID 区分不同用户
   - 或者完全禁用 Guest 用户，要求所有用户登录

3. **增强 API Key 管理**：
   - 实现 API Key 的撤销和禁用功能
   - 添加 API Key 的权限范围限制
   - 实现 API Key 的使用配额限制

## 9. 总结

### 9.1 授权验证的作用

1. **保护项目数据**：确保只有授权用户才能访问项目
2. **支持 API 访问**：通过 API Key 支持程序化访问
3. **资源隔离**：不同用户的数据相互隔离

### 9.2 用户类型

1. **Guest 用户**：在 `USE_AUTH=false` 时使用，不需要登录
2. **普通用户**：通过 Auth0 认证的用户，需要登录
3. **项目成员**：拥有项目访问权限的用户
4. **API Key**：用于程序化访问项目的密钥

### 9.3 功能差异

- **Guest 用户 vs 普通用户**：主要区别在于是否需要登录和多用户支持
- **项目成员 vs API Key**：主要区别在于访问方式和使用场景
- **所有项目成员权限相同**：目前没有实现角色区分

### 9.4 当前配置

- **USE_AUTH=false**：使用 Guest 用户，不需要登录
- **适合场景**：开发、测试、演示环境
- **不适合场景**：多用户生产环境

---

**文档版本**：v1.0  
**最后更新**：2025-01-27  
**维护者**：开发团队

