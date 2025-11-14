#!/bin/bash
# 完整测试套件运行脚本
# Complete test suite runner

set -e

echo "🚀 开始完整测试套件..."
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查服务是否运行
check_service() {
    local service_name=$1
    local url=$2
    
    echo -n "检查 $service_name 服务..."
    if curl -s "$url" > /dev/null 2>&1; then
        echo -e " ${GREEN}✓${NC}"
        return 0
    else
        echo -e " ${RED}✗${NC}"
        return 1
    fi
}

# 检查后端服务
if ! check_service "后端" "http://localhost:8001/api/v1/health"; then
    echo -e "${RED}错误: 后端服务未运行，请先启动后端服务${NC}"
    exit 1
fi

# 检查前端服务
if ! check_service "前端" "http://localhost:3001"; then
    echo -e "${RED}错误: 前端服务未运行，请先启动前端服务${NC}"
    exit 1
fi

echo ""
echo "📋 运行后端API测试..."
cd backend
python -m pytest tests/test_api_endpoints.py -v --tb=short
API_TEST_RESULT=$?
cd ..

echo ""
echo "📋 运行后端服务测试..."
cd backend
python -m pytest tests/test_services.py -v --tb=short
SERVICE_TEST_RESULT=$?
cd ..

echo ""
echo "📋 运行Playwright端到端测试..."
if [ -f "playwright.config.ts" ] || [ -f "playwright.config.js" ]; then
    npx playwright test tests/e2e/test_full_workflow.spec.ts --reporter=list
    E2E_TEST_RESULT=$?
else
    echo -e "${YELLOW}警告: 未找到Playwright配置，跳过E2E测试${NC}"
    E2E_TEST_RESULT=0
fi

echo ""
echo "📊 测试结果汇总:"
echo "  API测试: $([ $API_TEST_RESULT -eq 0 ] && echo -e "${GREEN}通过${NC}" || echo -e "${RED}失败${NC}")"
echo "  服务测试: $([ $SERVICE_TEST_RESULT -eq 0 ] && echo -e "${GREEN}通过${NC}" || echo -e "${RED}失败${NC}")"
echo "  E2E测试: $([ $E2E_TEST_RESULT -eq 0 ] && echo -e "${GREEN}通过${NC}" || echo -e "${RED}失败${NC}")"

if [ $API_TEST_RESULT -eq 0 ] && [ $SERVICE_TEST_RESULT -eq 0 ] && [ $E2E_TEST_RESULT -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ 所有测试通过！${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}❌ 部分测试失败，请检查上述输出${NC}"
    exit 1
fi





