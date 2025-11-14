#!/bin/bash
# 查看 Copilot 日志脚本
# View Copilot logs script

LOG_FILE="/tmp/backend_copilot.log"

echo "🔍 查看 Copilot 日志..."
echo "📂 日志文件: $LOG_FILE"
echo ""

if [ ! -f "$LOG_FILE" ]; then
    echo "⚠️ 日志文件尚未创建"
    echo "💡 请先触发一个 Copilot 请求（在前端输入'搜索相关工具'等）"
    echo ""
    echo "等待日志文件创建..."
    while [ ! -f "$LOG_FILE" ]; do
        sleep 1
    done
    echo "✅ 日志文件已创建"
    echo ""
fi

echo "📋 最近的日志（最后 100 行）:"
echo "---"
tail -n 100 "$LOG_FILE"

echo ""
echo ""
echo "💡 实时查看日志（按 Ctrl+C 退出）:"
echo "   tail -f $LOG_FILE"
echo ""
echo "💡 过滤关键信息:"
echo "   tail -f $LOG_FILE | grep -E '迭代|AIMessage|ToolMessage|错误|警告|✅|❌'"

