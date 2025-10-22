#!/bin/bash
# nb_proxypool 一键启动脚本

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PID_DIR="$PROJECT_ROOT/.pids"

# 创建 PID 目录
mkdir -p "$PID_DIR"

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════╗"
echo "║     nb_proxypool 代理池管理系统           ║"
echo "║           一键启动脚本                    ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# 检查 .env 文件
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${YELLOW}⚠️  未找到 .env 配置文件${NC}"
    echo -e "${YELLOW}   正在从 env.example 创建...${NC}"
    cp "$PROJECT_ROOT/env.example" "$PROJECT_ROOT/.env"
    echo -e "${GREEN}✅ 已创建 .env 文件，请根据实际情况修改配置${NC}"
    echo ""
fi

# 进入项目目录
cd "$PROJECT_ROOT"

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ 错误：未找到 uv 命令${NC}"
    echo "   请先安装 uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 添加 uv 到 PATH
export PATH="$HOME/.local/bin:$PATH"

# ==================== 启动后端 API ====================
echo -e "${GREEN}[1/2] 启动后端 API 服务...${NC}"

API_PID_FILE="$PID_DIR/api.pid"

# 检查是否已在运行
if [ -f "$API_PID_FILE" ] && kill -0 $(cat "$API_PID_FILE") 2>/dev/null; then
    echo -e "${YELLOW}   后端 API 已在运行 (PID: $(cat "$API_PID_FILE"))${NC}"
else
    # 启动 API 服务
    nohup uv run uvicorn backend.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload \
        > "$PID_DIR/api.log" 2>&1 &
    
    API_PID=$!
    echo $API_PID > "$API_PID_FILE"
    
    echo -e "${GREEN}✅ 后端 API 已启动 (PID: $API_PID)${NC}"
    echo -e "${BLUE}   访问地址: http://localhost:8000${NC}"
    echo -e "${BLUE}   API 文档: http://localhost:8000/docs${NC}"
fi

# ==================== 启动前端（如果存在）====================
echo -e "\n${GREEN}[2/2] 检查前端服务...${NC}"

FRONTEND_DIR="$PROJECT_ROOT/frontend"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"

if [ -d "$FRONTEND_DIR" ] && [ -f "$FRONTEND_DIR/package.json" ]; then
    # 检查是否已在运行
    if [ -f "$FRONTEND_PID_FILE" ] && kill -0 $(cat "$FRONTEND_PID_FILE") 2>/dev/null; then
        echo -e "${YELLOW}   前端服务已在运行 (PID: $(cat "$FRONTEND_PID_FILE"))${NC}"
    else
        # 检查依赖是否安装
        if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
            echo -e "${YELLOW}   安装前端依赖...${NC}"
            cd "$FRONTEND_DIR"
            npm install
            cd "$PROJECT_ROOT"
        fi
        
        # 启动前端
        cd "$FRONTEND_DIR"
        nohup npm run dev > "$PID_DIR/frontend.log" 2>&1 &
        FRONTEND_PID=$!
        echo $FRONTEND_PID > "$FRONTEND_PID_FILE"
        cd "$PROJECT_ROOT"
        
        echo -e "${GREEN}✅ 前端服务已启动 (PID: $FRONTEND_PID)${NC}"
        echo -e "${BLUE}   访问地址: http://localhost:5173${NC}"
    fi
else
    echo -e "${YELLOW}   前端项目未找到，跳过${NC}"
    echo -e "${YELLOW}   （前端功能稍后完成）${NC}"
fi

# ==================== 完成 ====================
echo -e "\n${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         🎉 所有服务启动完成！             ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"

echo -e "\n${BLUE}📌 访问地址：${NC}"
echo -e "   后端 API: ${GREEN}http://localhost:8000${NC}"
echo -e "   API 文档: ${GREEN}http://localhost:8000/docs${NC}"
if [ -d "$FRONTEND_DIR" ]; then
    echo -e "   前端界面: ${GREEN}http://localhost:5173${NC}"
fi

echo -e "\n${BLUE}📌 管理命令：${NC}"
echo -e "   查看日志: ${YELLOW}tail -f $PID_DIR/api.log${NC}"
echo -e "   停止服务: ${YELLOW}bash scripts/stop.sh${NC}"

echo -e "\n${YELLOW}💡 提示：${NC}"
echo -e "   - 首次使用请先配置 Redis 连接（编辑 .env 文件）"
echo -e "   - 通过 Web 界面或 API 启动爬虫"
echo -e ""

