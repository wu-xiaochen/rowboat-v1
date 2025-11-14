#!/bin/bash
# 手动API测试脚本（不依赖pytest）
# Manual API testing script (without pytest dependency)

set -e

echo "🧪 手动API测试..."
echo ""

BASE_URL="http://localhost:8001/api/v1"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 测试健康检查
echo "1. 测试健康检查端点..."
HEALTH_RESPONSE=$(curl -s "$BASE_URL/health")
if echo "$HEALTH_RESPONSE" | grep -q '"success":true'; then
    STATUS=$(echo "$HEALTH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['status'])" 2>/dev/null || echo "unknown")
    if [ "$STATUS" = "healthy" ] || [ "$STATUS" = "degraded" ]; then
        echo -e "  ${GREEN}✓${NC} 健康检查通过 (状态: $STATUS)"
    else
        echo -e "  ${YELLOW}⚠${NC} 健康检查响应异常: $STATUS"
    fi
else
    echo -e "  ${RED}✗${NC} 健康检查失败"
    exit 1
fi

# 测试ping
echo ""
echo "2. 测试ping端点..."
PING_RESPONSE=$(curl -s "$BASE_URL/health/ping")
if echo "$PING_RESPONSE" | grep -q '"success":true'; then
    PING_VALUE=$(echo "$PING_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('data', {}).get('ping', 'unknown'))" 2>/dev/null || echo "unknown")
    if [ "$PING_VALUE" = "pong" ]; then
        echo -e "  ${GREEN}✓${NC} Ping测试通过 (响应: $PING_VALUE)"
    else
        echo -e "  ${YELLOW}⚠${NC} Ping响应异常: $PING_VALUE"
    fi
else
    echo -e "  ${RED}✗${NC} Ping测试失败"
    echo "  响应: $(echo "$PING_RESPONSE" | python3 -m json.tool 2>/dev/null | head -3)"
fi

# 测试API信息
echo ""
echo "3. 测试API信息端点..."
INFO_RESPONSE=$(curl -s "$BASE_URL/info")
if echo "$INFO_RESPONSE" | grep -q '"success":true'; then
    NAME=$(echo "$INFO_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['name'])" 2>/dev/null || echo "unknown")
    VERSION=$(echo "$INFO_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['version'])" 2>/dev/null || echo "unknown")
    echo -e "  ${GREEN}✓${NC} API信息测试通过 (名称: $NAME, 版本: $VERSION)"
else
    echo -e "  ${RED}✗${NC} API信息测试失败"
fi

# 测试创建项目
echo ""
echo "4. 测试创建项目端点..."
PROJECT_DATA='{"name":"API测试项目","mode":{"workflowJson":"{\"agents\":[],\"tools\":[],\"prompts\":[],\"pipelines\":[],\"startAgent\":null}"}}'
CREATE_RESPONSE=$(curl -s -X POST "$BASE_URL/projects" \
    -H "Content-Type: application/json" \
    -d "$PROJECT_DATA")

if echo "$CREATE_RESPONSE" | grep -q '"success":true'; then
    PROJECT_ID=$(echo "$CREATE_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('data', {}).get('id') or d.get('id', ''))" 2>/dev/null || echo "")
    if [ -n "$PROJECT_ID" ]; then
        echo -e "  ${GREEN}✓${NC} 创建项目成功 (ID: $PROJECT_ID)"
        
        # 清理：删除测试项目
        echo ""
        echo "5. 测试删除项目端点..."
        DELETE_RESPONSE=$(curl -s -X DELETE "$BASE_URL/projects/$PROJECT_ID")
        if echo "$DELETE_RESPONSE" | grep -q '"success":true' || [ "$(echo "$DELETE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status_code', 0))" 2>/dev/null || echo 0)" = "204" ]; then
            echo -e "  ${GREEN}✓${NC} 删除项目成功"
        else
            echo -e "  ${YELLOW}⚠${NC} 删除项目响应异常（可能已删除）"
        fi
    else
        echo -e "  ${YELLOW}⚠${NC} 创建项目成功但未获取到ID"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} 创建项目失败或需要认证"
    echo "  响应: $(echo "$CREATE_RESPONSE" | python3 -m json.tool 2>/dev/null | head -5)"
fi

echo ""
echo -e "${GREEN}✅ 手动API测试完成！${NC}"

