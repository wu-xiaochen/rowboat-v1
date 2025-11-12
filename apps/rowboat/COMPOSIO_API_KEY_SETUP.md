# Composio API密钥配置说明
# Composio API Key Setup Guide

## 问题描述

前端代码直接调用Composio API，需要配置Composio API密钥。

## 配置方法

### 1. 创建或编辑 `.env.local` 文件

在 `apps/rowboat/` 目录下创建或编辑 `.env.local` 文件：

```bash
# Composio API密钥（用于前端直接调用Composio API）
NEXT_PUBLIC_COMPOSIO_API_KEY=ak_KOSnpLA9q1ceJCjkKIKa
```

### 2. 重启开发服务器

配置环境变量后，需要重启Next.js开发服务器：

```bash
cd apps/rowboat
npm run dev
```

## 注意事项

1. **环境变量前缀**：前端客户端代码只能访问 `NEXT_PUBLIC_` 前缀的环境变量
2. **服务器端代码**：可以使用 `COMPOSIO_API_KEY`（不带前缀）
3. **安全性**：`NEXT_PUBLIC_` 前缀的变量会暴露到客户端，请确保API密钥可以公开使用

## 当前配置

根据项目规则文档，Composio API密钥为：
```
ak_KOSnpLA9q1ceJCjkKIKa
```

## 验证配置

配置完成后，触发器管理页面应该能够正常加载Composio工具包列表，不再出现401错误。

---

**文档版本**：v1.0  
**最后更新**：2025-01-27

