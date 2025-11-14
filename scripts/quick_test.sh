#!/bin/bash
# 快速测试脚本 - 验证基础功能
# Quick test script - verify basic functionality

set -e

echo "🚀 快速测试 - 验证基础功能..."
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 测试后端健康检查
echo "1. 测试后端健康检查..."
if curl -s http://localhost:8001/api/v1/health > /dev/null 2>&1; then
    HEALTH_RESPONSE=$(curl -s http://localhost:8001/api/v1/health)
    if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
        echo -e "  ${GREEN}✓${NC} 后端服务健康"
    else
        echo -e "  ${YELLOW}⚠${NC} 后端服务响应异常: $HEALTH_RESPONSE"
    fi
else
    echo -e "  ${RED}✗${NC} 后端服务未运行"
    echo "  请运行: cd backend && uvicorn app.main:app --reload --port 8001"
    exit 1
fi

# 测试前端
echo ""
echo "2. 测试前端服务..."
if curl -s http://localhost:3001 > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} 前端服务运行中"
else
    echo -e "  ${RED}✗${NC} 前端服务未运行"
    echo "  请运行: cd apps/rowboat && npm run dev"
    exit 1
fi

# 测试API信息
echo ""
echo "3. 测试API信息端点..."
API_INFO=$(curl -s http://localhost:8001/api/v1/info)
if echo "$API_INFO" | grep -q "name"; then
    echo -e "  ${GREEN}✓${NC} API信息端点正常"
    echo "  响应: $API_INFO"
else
    echo -e "  ${YELLOW}⚠${NC} API信息端点响应异常: $API_INFO"
fi

# 检查遗留代码
echo ""
echo "4. 检查前端遗留代码..."
if [ -f "scripts/check_legacy_code.sh" ]; then
    bash scripts/check_legacy_code.sh 2>&1 | grep -E "发现|未发现" | head -5
else
    echo -e "  ${YELLOW}⚠${NC} 遗留代码检查脚本不存在"
fi

echo ""
echo "✅ 快速测试完成！"





