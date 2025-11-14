#!/bin/bash

# Copilot API 测试脚本
# 用于测试 Copilot 流式响应端点

set -e

PROJECT_ID="${1:-648cc3ed-ab31-4071-a220-8c32e3712c77}"
API_BASE_URL="${2:-http://localhost:8001}"

echo "🧪 Copilot API 测试"
echo "===================="
echo "项目ID: $PROJECT_ID"
echo "API地址: $API_BASE_URL"
echo ""

# 测试1: 健康检查
echo "📋 测试1: 健康检查"
HEALTH_RESPONSE=$(curl -s "$API_BASE_URL/api/v1/health")
HEALTH_STATUS=$(echo "$HEALTH_RESPONSE" | jq -r '.data.status' 2>/dev/null || echo "unknown")
if [ "$HEALTH_STATUS" = "healthy" ]; then
    echo "✅ 后端服务健康"
else
    echo "❌ 后端服务不健康: $HEALTH_STATUS"
    exit 1
fi
echo ""

# 测试2: 简单对话（无工具调用）
echo "📋 测试2: 简单对话（无工具调用）"
echo "发送消息: '你好，请介绍一下你自己'"
echo ""

REQUEST_BODY=$(cat <<EOF
{
  "projectId": "$PROJECT_ID",
  "messages": [
    {
      "role": "user",
      "content": "你好，请介绍一下你自己"
    }
  ],
  "workflow": {
    "agents": []
  }
}
EOF
)

echo "请求体:"
echo "$REQUEST_BODY" | jq .
echo ""
echo "响应（前10行）:"
curl -s -X POST "$API_BASE_URL/api/v1/$PROJECT_ID/copilot/stream" \
  -H "Content-Type: application/json" \
  -d "$REQUEST_BODY" | head -20 || echo "❌ 请求失败"
echo ""
echo ""

# 测试3: 工具调用（单轮）
echo "📋 测试3: 工具调用（单轮）"
echo "发送消息: '搜索邮件发送相关的工具'"
echo ""

REQUEST_BODY_TOOL=$(cat <<EOF
{
  "projectId": "$PROJECT_ID",
  "messages": [
    {
      "role": "user",
      "content": "搜索邮件发送相关的工具"
    }
  ],
  "workflow": {
    "agents": []
  }
}
EOF
)

echo "请求体:"
echo "$REQUEST_BODY_TOOL" | jq .
echo ""
echo "响应（前30行，查找 tool-call 事件）:"
curl -s -X POST "$API_BASE_URL/api/v1/$PROJECT_ID/copilot/stream" \
  -H "Content-Type: application/json" \
  -d "$REQUEST_BODY_TOOL" | head -30 || echo "❌ 请求失败"
echo ""
echo ""

echo "✅ 测试完成"
echo ""
echo "📝 注意："
echo "1. 完整测试需要在前端界面进行"
echo "2. 请启动前端服务：cd apps/rowboat && npm run dev"
echo "3. 访问 http://localhost:3001 进行完整测试"

