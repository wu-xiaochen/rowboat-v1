#!/bin/bash
# 日志监控脚本
# Log Monitoring Script

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志文件路径
BACKEND_LOG="/tmp/backend.log"
FRONTEND_LOG="/tmp/frontend.log"

echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}   服务日志监控${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""

# 检查日志文件是否存在
if [ ! -f "$BACKEND_LOG" ]; then
    echo -e "${YELLOW}⚠️  后端日志文件不存在，正在创建...${NC}"
    touch "$BACKEND_LOG"
fi

if [ ! -f "$FRONTEND_LOG" ]; then
    echo -e "${YELLOW}⚠️  前端日志文件不存在，正在创建...${NC}"
    touch "$FRONTEND_LOG"
fi

# 显示最近日志
echo -e "${GREEN}📋 后端最近日志 (最后20行):${NC}"
echo -e "${BLUE}───────────────────────────────────────${NC}"
tail -20 "$BACKEND_LOG" 2>/dev/null || echo "暂无日志"
echo ""

echo -e "${GREEN}📋 前端最近日志 (最后20行):${NC}"
echo -e "${BLUE}───────────────────────────────────────${NC}"
tail -20 "$FRONTEND_LOG" 2>/dev/null || echo "暂无日志"
echo ""

# 实时监控选项
echo -e "${YELLOW}选择监控模式:${NC}"
echo "1) 监控后端日志 (实时)"
echo "2) 监控前端日志 (实时)"
echo "3) 同时监控后端和前端日志 (实时)"
echo "4) 查看后端日志 (最后50行)"
echo "5) 查看前端日志 (最后50行)"
echo "6) 退出"
echo ""

read -p "请选择 (1-6): " choice

case $choice in
    1)
        echo -e "${GREEN}开始监控后端日志... (按 Ctrl+C 退出)${NC}"
        tail -f "$BACKEND_LOG"
        ;;
    2)
        echo -e "${GREEN}开始监控前端日志... (按 Ctrl+C 退出)${NC}"
        tail -f "$FRONTEND_LOG"
        ;;
    3)
        echo -e "${GREEN}开始同时监控后端和前端日志... (按 Ctrl+C 退出)${NC}"
        tail -f "$BACKEND_LOG" "$FRONTEND_LOG"
        ;;
    4)
        echo -e "${GREEN}后端日志 (最后50行):${NC}"
        tail -50 "$BACKEND_LOG"
        ;;
    5)
        echo -e "${GREEN}前端日志 (最后50行):${NC}"
        tail -50 "$FRONTEND_LOG"
        ;;
    6)
        echo "退出监控"
        exit 0
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac

