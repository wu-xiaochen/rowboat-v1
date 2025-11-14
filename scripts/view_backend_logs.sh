#!/bin/bash
# 查看后端服务日志脚本
# View backend service logs script

echo "🔍 查找后端服务进程..."
PID=$(ps aux | grep -E "uvicorn.*8001" | grep -v grep | awk '{print $2}' | head -1)

if [ -z "$PID" ]; then
    echo "❌ 未找到运行中的后端服务"
    exit 1
fi

echo "✅ 找到后端服务进程: $PID"
echo "📂 工作目录: $(lsof -p $PID -a -d cwd 2>/dev/null | tail -1 | awk '{print $NF}')"
echo ""
echo "📋 查看最近的系统日志（包含 copilot/tool 相关）..."
echo "---"

# 尝试查看系统日志
if command -v log &> /dev/null; then
    log show --predicate "process == 'python' AND eventMessage contains 'copilot' OR eventMessage contains 'tool' OR eventMessage contains 'AIMessage' OR eventMessage contains 'ToolMessage' OR eventMessage contains '迭代'" --last 10m --style compact 2>/dev/null | tail -100
else
    echo "⚠️ 无法使用 log 命令，尝试其他方法..."
    echo ""
    echo "💡 建议："
    echo "1. 如果后端服务在终端运行，直接查看终端输出"
    echo "2. 如果使用 screen/tmux，切换到相应会话查看"
    echo "3. 重新启动服务并重定向输出："
    echo "   cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8001 2>&1 | tee /tmp/backend_copilot.log"
    echo ""
    echo "4. 或者触发一个 Copilot 请求，然后查看进程输出"
fi

echo ""
echo "🔍 检查是否有日志文件..."
find /Users/xiaochenwu/Desktop/rowboat/backend -name "*.log" -o -name "nohup.out" 2>/dev/null | head -5

echo ""
echo "💡 实时查看日志（如果服务输出到文件）："
echo "   tail -f /tmp/backend_copilot.log"

