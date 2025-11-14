#!/bin/bash
# 运行所有测试脚本
# Run all test scripts

set -e

echo "🧪 运行完整测试套件..."
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASSED=0
FAILED=0
SKIPPED=0

# 测试函数
run_test() {
    local test_name=$1
    local test_command=$2
    
    echo -n "运行: $test_name... "
    if eval "$test_command" > /tmp/test_output.log 2>&1; then
        echo -e "${GREEN}✓${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC}"
        echo "  错误输出:"
        tail -5 /tmp/test_output.log | sed 's/^/    /'
        ((FAILED++))
        return 1
    fi
}

# 1. 快速测试
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. 快速测试"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
run_test "快速测试" "bash scripts/quick_test.sh"

# 2. 手动API测试
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. 手动API测试"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
run_test "手动API测试" "bash scripts/test_api_manually.sh"

# 3. 遗留代码检查
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. 遗留代码检查"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
run_test "遗留代码检查" "bash scripts/check_legacy_code.sh"

# 4. 服务健康检查
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. 服务健康检查"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if curl -s http://localhost:8001/api/v1/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} 后端服务运行中"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} 后端服务未运行"
    ((FAILED++))
fi

if curl -s http://localhost:3001 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} 前端服务运行中"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} 前端服务未运行"
    ((FAILED++))
fi

# 总结
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 测试结果汇总"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "通过: ${GREEN}$PASSED${NC}"
echo "失败: ${RED}$FAILED${NC}"
echo "跳过: ${YELLOW}$SKIPPED${NC}"

TOTAL=$((PASSED + FAILED + SKIPPED))
if [ $TOTAL -gt 0 ]; then
    PASS_RATE=$((PASSED * 100 / TOTAL))
    echo "通过率: ${PASS_RATE}%"
fi

echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ 所有测试通过！${NC}"
    exit 0
else
    echo -e "${RED}❌ 部分测试失败${NC}"
    exit 1
fi





