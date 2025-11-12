#!/bin/bash
# 启动开发服务脚本
# Start development services script

echo "正在启动开发服务..."

# 检查端口是否被占用
if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  端口8001已被占用，后端服务可能已在运行"
else
    echo "启动后端服务（端口8001）..."
    cd backend
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload > /tmp/backend.log 2>&1 &
    BACKEND_PID=$!
    echo "后端服务已启动 (PID: $BACKEND_PID)"
    cd ..
fi

# 等待后端启动
sleep 3

# 检查后端健康状态
if curl -s http://localhost:8001/api/v1/health > /dev/null 2>&1; then
    echo "✅ 后端服务健康检查通过"
else
    echo "⚠️  后端服务健康检查失败，请检查日志: tail -f /tmp/backend.log"
fi

# 检查端口是否被占用
if lsof -Pi :3001 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  端口3001已被占用，前端服务可能已在运行"
else
    echo "启动前端服务（端口3001）..."
    cd apps/rowboat
    npm run dev > /tmp/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "前端服务已启动 (PID: $FRONTEND_PID)"
    cd ../..
fi

# 等待前端启动
sleep 5

# 检查前端是否可访问
if curl -s http://localhost:3001 > /dev/null 2>&1; then
    echo "✅ 前端服务可访问"
else
    echo "⚠️  前端服务不可访问，请检查日志: tail -f /tmp/frontend.log"
fi

echo ""
echo "服务启动完成！"
echo "后端日志: tail -f /tmp/backend.log"
echo "前端日志: tail -f /tmp/frontend.log"
echo ""
echo "按 Ctrl+C 停止服务"

# 等待用户中断
wait

