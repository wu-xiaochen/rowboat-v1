#!/bin/bash
# 使用Playwright MCP运行测试并自动修复
# Run tests with Playwright MCP and auto-fix

set -e

echo "🎯 开始Playwright MCP测试..."
echo ""

cd "$(dirname "$0")/.."

# 检查服务
echo "1. 检查服务状态..."
if ! curl -s http://localhost:8001/api/v1/health > /dev/null 2>&1; then
    echo "❌ 后端服务未运行"
    exit 1
fi

if ! curl -s http://localhost:3001 > /dev/null 2>&1; then
    echo "❌ 前端服务未运行"
    exit 1
fi

echo "✅ 服务运行正常"
echo ""

# 运行测试（最多重试5次）
MAX_RETRIES=5
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "测试运行 #$((RETRY_COUNT + 1))"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    cd apps/rowboat
    
    # 运行测试
    if npx playwright test ../tests/e2e/test_playwright_mcp_coverage.spec.ts --reporter=list --workers=1 --timeout=90000 2>&1 | tee /tmp/test_output.log; then
        echo ""
        echo "✅ 所有测试通过！"
        exit 0
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo ""
        echo "⚠️ 测试失败，尝试修复..."
        echo ""
        
        # 分析失败原因
        FAILED_TESTS=$(grep -E "^\s+[0-9]+\)" /tmp/test_output.log | head -5)
        echo "失败的测试:"
        echo "$FAILED_TESTS"
        echo ""
        
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo "等待5秒后重试..."
            sleep 5
        fi
    fi
done

echo ""
echo "❌ 测试失败，已达到最大重试次数"
exit 1





