#!/bin/bash
# Playwright端到端测试运行脚本
# Playwright end-to-end test runner

set -e

echo "🎭 运行Playwright端到端测试..."
echo ""

# 检查Playwright是否安装
if ! command -v npx &> /dev/null; then
    echo "错误: 未找到npx，请先安装Node.js"
    exit 1
fi

# 检查playwright是否安装
if [ ! -d "node_modules/@playwright" ] && [ ! -d "apps/rowboat/node_modules/@playwright" ]; then
    echo "📦 安装Playwright..."
    if [ -f "apps/rowboat/package.json" ]; then
        cd apps/rowboat
        npm install -D @playwright/test playwright
        npx playwright install chromium
        cd ../..
    else
        npm install -D @playwright/test playwright
        npx playwright install chromium
    fi
fi

# 运行测试
echo "🚀 开始运行Playwright测试..."
if [ -f "apps/rowboat/package.json" ]; then
    cd apps/rowboat
    npx playwright test ../tests/e2e/test_full_workflow.spec.ts --reporter=list,html
else
    npx playwright test tests/e2e/test_full_workflow.spec.ts --reporter=list,html
fi

echo ""
echo "✅ Playwright测试完成！"
echo "查看详细报告: playwright-report/index.html"





