#!/bin/bash
# nb_proxypool 停止脚本

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PID_DIR="$PROJECT_ROOT/.pids"

echo -e "${YELLOW}正在停止 nb_proxypool 所有服务...${NC}\n"

# 停止后端 API
API_PID_FILE="$PID_DIR/api.pid"
if [ -f "$API_PID_FILE" ]; then
    PID=$(cat "$API_PID_FILE")
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo -e "${GREEN}✅ 后端 API 已停止 (PID: $PID)${NC}"
    else
        echo -e "${YELLOW}   后端 API 未运行${NC}"
    fi
    rm -f "$API_PID_FILE"
else
    echo -e "${YELLOW}   后端 API 未运行${NC}"
fi

# 停止前端
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"
if [ -f "$FRONTEND_PID_FILE" ]; then
    PID=$(cat "$FRONTEND_PID_FILE")
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo -e "${GREEN}✅ 前端服务已停止 (PID: $PID)${NC}"
    else
        echo -e "${YELLOW}   前端服务未运行${NC}"
    fi
    rm -f "$FRONTEND_PID_FILE"
else
    echo -e "${YELLOW}   前端服务未运行${NC}"
fi

# 清理日志（可选）
# rm -f "$PID_DIR"/*.log

echo -e "\n${GREEN}所有服务已停止！${NC}"

