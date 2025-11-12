#!/bin/bash
# 等待服务就绪脚本
# Wait for services to be ready

echo "等待服务启动..."

# 等待后端
echo -n "等待后端服务 (http://localhost:8001)..."
for i in {1..30}; do
    if curl -s http://localhost:8001/api/v1/health > /dev/null 2>&1; then
        echo " ✅ 就绪"
        break
    fi
    echo -n "."
    sleep 1
done

# 等待前端
echo -n "等待前端服务 (http://localhost:3001)..."
for i in {1..60}; do
    if curl -s http://localhost:3001 > /dev/null 2>&1; then
        echo " ✅ 就绪"
        break
    fi
    echo -n "."
    sleep 1
done

echo ""
echo "服务状态检查："
curl -s http://localhost:8001/api/v1/health | python3 -m json.tool 2>/dev/null | grep -E "(status|message)" | head -2 || echo "后端未就绪"
curl -s -o /dev/null -w "前端HTTP状态: %{http_code}\n" http://localhost:3001 2>&1

