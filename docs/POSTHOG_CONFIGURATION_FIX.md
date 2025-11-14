# PostHog 配置修复

## 问题描述

前端控制台出现以下警告：
```
[PostHog.js] PostHog was initialized without a token. This likely indicates a misconfiguration. Please check the first argument passed to posthog.init()
```

## 问题原因

在 `instrumentation-client.ts` 中，PostHog 被无条件初始化，即使 `NEXT_PUBLIC_POSTHOG_KEY` 环境变量未设置。这会导致 PostHog 在没有 token 的情况下尝试初始化，产生警告。

## 解决方案

### 1. 添加条件检查

只有在 PostHog token 存在时才初始化：

```typescript
const posthogKey = process.env.NEXT_PUBLIC_POSTHOG_KEY;

if (posthogKey && posthogKey.trim() !== '') {
    posthog.init(posthogKey, {
        api_host: posthogHost || 'https://app.posthog.com',
        defaults: '2025-05-24'
    });
} else {
    // PostHog is not configured, skip initialization
    if (process.env.NODE_ENV === 'development') {
        console.log('[PostHog] Skipping initialization: NEXT_PUBLIC_POSTHOG_KEY is not set');
    }
}
```

### 2. 提供默认值

为 `api_host` 提供默认值，避免未设置时的错误。

### 3. 开发环境友好提示

在开发环境中，如果 PostHog 未配置，显示友好的日志信息而不是警告。

## 修改文件

- `apps/rowboat/instrumentation-client.ts`
  - 添加 PostHog token 存在性检查
  - 只有在 token 存在时才初始化 PostHog
  - 添加开发环境的友好提示

## 配置 PostHog（可选）

如果需要使用 PostHog 分析功能，在 `.env.local` 中添加：

```bash
NEXT_PUBLIC_POSTHOG_KEY=your_posthog_key_here
NEXT_PUBLIC_POSTHOG_HOST=https://app.posthog.com  # 可选，默认为 https://app.posthog.com
```

## 验证

修复后：
1. ✅ 如果没有配置 PostHog token，不会显示警告
2. ✅ 如果配置了 PostHog token，正常初始化
3. ✅ 开发环境显示友好的提示信息

## 最佳实践

1. **条件初始化**：对于可选的分析工具，应该检查配置是否存在再初始化
2. **环境变量验证**：在使用环境变量前，检查其是否存在且非空
3. **开发体验**：在开发环境中提供清晰的提示，说明为什么某些功能未启用
4. **生产环境**：在生产环境中，静默跳过未配置的功能，避免控制台噪音

## 相关文件

- `apps/rowboat/instrumentation-client.ts` - PostHog 初始化代码
- `.env.local` - 环境变量配置（需要手动创建和配置）

