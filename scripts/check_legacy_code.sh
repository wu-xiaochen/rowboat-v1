#!/bin/bash
# 检查前端残留的旧后端代码
# Check for legacy backend code in frontend

echo "🔍 检查前端残留的旧后端代码..."
echo ""

cd "$(dirname "$0")/.."

# 检查旧的PROVIDER_*变量
echo "检查旧的PROVIDER_*环境变量..."
LEGACY_PROVIDER=$(grep -r "PROVIDER_API_KEY\|PROVIDER_BASE_URL\|PROVIDER_DEFAULT_MODEL" apps/rowboat --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" 2>/dev/null | grep -v node_modules | grep -v ".next" | grep -v "DEPRECATED" | grep -v "已弃用" || true)

if [ -n "$LEGACY_PROVIDER" ]; then
    echo "⚠️ 发现旧的PROVIDER_*变量:"
    echo "$LEGACY_PROVIDER" | head -10
    if [ $(echo "$LEGACY_PROVIDER" | wc -l) -gt 10 ]; then
        echo "... (还有更多)"
    fi
else
    echo "✅ 未发现旧的PROVIDER_*变量"
fi

echo ""

# 检查旧的agents runtime导入
echo "检查旧的agents runtime导入..."
LEGACY_AGENTS=$(grep -r "from.*agents-runtime.*agents\|streamResponse\|getResponse.*agents" apps/rowboat --include="*.ts" --include="*.tsx" 2>/dev/null | grep -v node_modules | grep -v ".next" | grep -v "DEPRECATED" | grep -v "已弃用" || true)

if [ -n "$LEGACY_AGENTS" ]; then
    echo "⚠️ 发现旧的agents runtime代码:"
    echo "$LEGACY_AGENTS" | head -10
    if [ $(echo "$LEGACY_AGENTS" | wc -l) -gt 10 ]; then
        echo "... (还有更多)"
    fi
else
    echo "✅ 未发现旧的agents runtime代码"
fi

echo ""

# 检查旧的路由
echo "检查旧的路由..."
LEGACY_ROUTES=$(grep -r "widget/v1/chats\|twilio/turn" apps/rowboat/app/api --include="route.ts" 2>/dev/null | grep -v "501\|Not implemented\|DEPRECATED\|已弃用" || true)

if [ -n "$LEGACY_ROUTES" ]; then
    echo "⚠️ 发现未正确禁用的旧路由:"
    echo "$LEGACY_ROUTES" | head -10
    if [ $(echo "$LEGACY_ROUTES" | wc -l) -gt 10 ]; then
        echo "... (还有更多)"
    fi
else
    echo "✅ 所有旧路由都已正确禁用"
fi

echo ""
echo "检查完成"

