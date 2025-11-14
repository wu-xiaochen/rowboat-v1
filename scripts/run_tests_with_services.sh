#!/bin/bash
# 运行测试前启动前后端服务
# Start frontend and backend services before running tests

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BACKEND_PORT=8001
FRONTEND_PORT=3001
BACKEND_URL="http://localhost:${BACKEND_PORT}"
FRONTEND_URL="http://localhost:${FRONTEND_PORT}"

# 清理函数
cleanup() {
    echo ""
    echo -e "${YELLOW}正在清理服务...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo "后端服务已停止"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo "前端服务已停止"
    fi
    exit 0
}

# 捕获中断信号
trap cleanup INT TERM

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}启动测试环境${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 检查并启动后端服务
echo -e "${YELLOW}检查后端服务...${NC}"
if lsof -Pi :${BACKEND_PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} 后端服务已在端口 ${BACKEND_PORT} 运行"
else
    echo -e "${YELLOW}启动后端服务（端口 ${BACKEND_PORT}）...${NC}"
    cd backend
    # 设置测试环境变量
    export ENVIRONMENT=test
    export DEBUG=true
    python -m uvicorn app.main:app --host 0.0.0.0 --port ${BACKEND_PORT} > /tmp/backend_test.log 2>&1 &
    BACKEND_PID=$!
    cd ..
    echo "后端服务已启动 (PID: $BACKEND_PID)"
    
    # 等待后端启动
    echo -e "${YELLOW}等待后端服务启动...${NC}"
    MAX_WAIT=30
    WAITED=0
    while [ $WAITED -lt $MAX_WAIT ]; do
        if curl -s ${BACKEND_URL}/api/v1/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} 后端服务健康检查通过"
            break
        fi
        sleep 1
        WAITED=$((WAITED + 1))
        echo -n "."
    done
    echo ""
    
    if [ $WAITED -eq $MAX_WAIT ]; then
        echo -e "${RED}✗${NC} 后端服务启动超时，请检查日志: tail -f /tmp/backend_test.log"
        cleanup
        exit 1
    fi
fi

# 检查并启动前端服务
echo -e "${YELLOW}检查前端服务...${NC}"
if lsof -Pi :${FRONTEND_PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} 前端服务已在端口 ${FRONTEND_PORT} 运行"
else
    echo -e "${YELLOW}启动前端服务（端口 ${FRONTEND_PORT}）...${NC}"
    cd apps/rowboat
    npm run dev > /tmp/frontend_test.log 2>&1 &
    FRONTEND_PID=$!
    cd ../..
    echo "前端服务已启动 (PID: $FRONTEND_PID)"
    
    # 等待前端启动
    echo -e "${YELLOW}等待前端服务启动...${NC}"
    MAX_WAIT=30
    WAITED=0
    while [ $WAITED -lt $MAX_WAIT ]; do
        if curl -s ${FRONTEND_URL} > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} 前端服务可访问"
            break
        fi
        sleep 1
        WAITED=$((WAITED + 1))
        echo -n "."
    done
    echo ""
    
    if [ $WAITED -eq $MAX_WAIT ]; then
        echo -e "${YELLOW}⚠${NC} 前端服务启动超时，但将继续运行测试"
    fi
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}运行测试${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 运行测试
cd backend
TEST_COMMAND="python -m pytest tests/ -v --tb=short --timeout=60 --timeout-method=thread"

if [ ! -z "$1" ]; then
    TEST_COMMAND="$TEST_COMMAND $@"
fi

echo -e "${YELLOW}执行测试命令: ${TEST_COMMAND}${NC}"
echo ""

# 运行测试
if eval "$TEST_COMMAND"; then
    TEST_RESULT=0
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ 所有测试通过！${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
else
    TEST_RESULT=1
    echo ""
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ 部分测试失败${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
fi

cd ..

# 清理服务
cleanup

exit $TEST_RESULT

