#!/bin/bash
# 运行100%覆盖测试
# Run 100% coverage tests

set -e

echo "🎯 运行100%覆盖测试..."
echo ""

cd "$(dirname "$0")/.."

# 检查服务
echo "1. 检查服务状态..."
if ! curl -s http://localhost:8001/api/v1/health > /dev/null 2>&1; then
    echo "❌ 后端服务未运行，请先启动"
    exit 1
fi

if ! curl -s http://localhost:3001 > /dev/null 2>&1; then
    echo "❌ 前端服务未运行，请先启动"
    exit 1
fi

echo "✅ 服务运行正常"
echo ""

# 运行Playwright测试
echo "2. 运行100%覆盖测试..."
cd apps/rowboat

if [ ! -d "node_modules/@playwright" ]; then
    echo "📦 安装Playwright..."
    npm install -D @playwright/test playwright
    npx playwright install chromium
fi

echo ""
echo "🚀 开始执行测试..."
echo ""

npx playwright test ../tests/e2e/test_100_percent_coverage.spec.ts --reporter=list,html

echo ""
echo "✅ 测试完成！"
echo "查看详细报告: playwright-report/index.html"





