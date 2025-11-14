#!/bin/bash
# 运行基础测试脚本
# Run basic tests script

set -e

echo "🧪 运行基础测试..."
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查服务
echo "1. 检查服务状态..."
if curl -s http://localhost:8001/api/v1/health > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} 后端服务运行中"
else
    echo -e "  ${RED}✗${NC} 后端服务未运行"
    exit 1
fi

if curl -s http://localhost:3001 > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} 前端服务运行中"
else
    echo -e "  ${RED}✗${NC} 前端服务未运行"
    exit 1
fi

echo ""
echo "2. 运行健康检查测试..."
cd backend

# 检查pytest是否安装
if ! python3 -m pytest --version > /dev/null 2>&1; then
    echo -e "  ${YELLOW}⚠${NC} pytest未安装，尝试安装..."
    python3 -m pip install -q pytest pytest-asyncio httpx
fi

# 运行健康检查测试
if python3 -m pytest tests/test_api_endpoints_comprehensive.py::TestHealthEndpoints -v --tb=short 2>&1; then
    echo -e "  ${GREEN}✓${NC} 健康检查测试通过"
else
    echo -e "  ${RED}✗${NC} 健康检查测试失败"
    exit 1
fi

echo ""
echo "3. 运行API信息测试..."
if python3 -m pytest tests/test_api_endpoints_comprehensive.py::TestInfoEndpoints -v --tb=short 2>&1; then
    echo -e "  ${GREEN}✓${NC} API信息测试通过"
else
    echo -e "  ${RED}✗${NC} API信息测试失败"
    exit 1
fi

cd ..
echo ""
echo -e "${GREEN}✅ 基础测试完成！${NC}"

