#!/bin/bash
# nb_proxypool 统一管理脚本
# 作者：nb_proxypool
# 版本：2.0.0

set -e

# ==================== 配置 ====================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PID_DIR="$PROJECT_ROOT/.pids"
LOG_DIR="$PROJECT_ROOT/logs"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 创建必要目录
mkdir -p "$PID_DIR" "$LOG_DIR"

# ==================== 工具函数 ====================

print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════╗"
    echo "║     nb_proxypool 代理池管理系统           ║"
    echo "║              v2.0.0                      ║"
    echo "╚══════════════════════════════════════════╝"
    echo -e "${NC}"
}

load_env() {
    # 加载 .env 配置
    if [ -f "$PROJECT_ROOT/.env" ]; then
        export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
    else
        echo -e "${YELLOW}⚠️  未找到 .env 文件，使用默认配置${NC}"
    fi
    
    # 设置默认值
    API_PORT=${API_PORT:-8000}
    FRONTEND_PORT=${FRONTEND_PORT:-5173}
}

# ==================== 启动函数 ====================

start_backend() {
    echo -e "${GREEN}[1/2] 启动后端 API 服务...${NC}"
    
    API_PID_FILE="$PID_DIR/api.pid"
    
    # 检查是否已在运行
    if [ -f "$API_PID_FILE" ] && kill -0 $(cat "$API_PID_FILE") 2>/dev/null; then
        echo -e "${YELLOW}   后端 API 已在运行 (PID: $(cat "$API_PID_FILE"))${NC}"
        return 0
    fi
    
    # 添加 uv 到 PATH
    export PATH="$HOME/.local/bin:$PATH"
    
    # 启动后端
    cd "$PROJECT_ROOT"
    nohup uv run uvicorn backend.main:app \
        --host 0.0.0.0 \
        --port ${API_PORT} \
        --reload \
        > "$LOG_DIR/api.log" 2>&1 &
    
    API_PID=$!
    echo $API_PID > "$API_PID_FILE"
    
    # 等待启动
    sleep 2
    
    if kill -0 $API_PID 2>/dev/null; then
        echo -e "${GREEN}✅ 后端 API 启动成功 (PID: $API_PID)${NC}"
        echo -e "${CYAN}   访问地址: http://localhost:${API_PORT}${NC}"
        echo -e "${CYAN}   API 文档: http://localhost:${API_PORT}/docs${NC}"
        return 0
    else
        echo -e "${RED}❌ 后端 API 启动失败${NC}"
        echo -e "${YELLOW}   查看日志: tail -f $LOG_DIR/api.log${NC}"
        return 1
    fi
}

start_frontend() {
    echo -e "\n${GREEN}[2/2] 启动前端服务...${NC}"
    
    FRONTEND_DIR="$PROJECT_ROOT/frontend"
    FRONTEND_PID_FILE="$PID_DIR/frontend.pid"
    
    # 检查前端目录是否存在
    if [ ! -d "$FRONTEND_DIR" ]; then
        echo -e "${YELLOW}   前端目录不存在，跳过${NC}"
        return 0
    fi
    
    # 检查是否已在运行
    if [ -f "$FRONTEND_PID_FILE" ] && kill -0 $(cat "$FRONTEND_PID_FILE") 2>/dev/null; then
        echo -e "${YELLOW}   前端服务已在运行 (PID: $(cat "$FRONTEND_PID_FILE"))${NC}"
        return 0
    fi
    
    # 检查依赖
    if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
        echo -e "${YELLOW}   首次运行，正在安装前端依赖（可能需要几分钟）...${NC}"
        cd "$FRONTEND_DIR"
        npm install > "$LOG_DIR/npm_install.log" 2>&1
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ 前端依赖安装失败${NC}"
            echo -e "${YELLOW}   查看日志: cat $LOG_DIR/npm_install.log${NC}"
            return 1
        fi
    fi
    
    # 启动前端
    cd "$FRONTEND_DIR"
    nohup npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$FRONTEND_PID_FILE"
    cd "$PROJECT_ROOT"
    
    # 等待启动
    sleep 2
    
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${GREEN}✅ 前端服务启动成功 (PID: $FRONTEND_PID)${NC}"
        echo -e "${CYAN}   访问地址: http://localhost:${FRONTEND_PORT}${NC}"
        return 0
    else
        echo -e "${RED}❌ 前端服务启动失败${NC}"
        echo -e "${YELLOW}   查看日志: tail -f $LOG_DIR/frontend.log${NC}"
        return 1
    fi
}

start_all() {
    print_header
    load_env
    
    # 检查 .env 文件
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        echo -e "${YELLOW}⚠️  未找到 .env 配置文件${NC}"
        echo -e "${YELLOW}   正在从 env.example 创建...${NC}"
        cp "$PROJECT_ROOT/env.example" "$PROJECT_ROOT/.env"
        echo -e "${GREEN}✅ 已创建 .env 文件${NC}"
        echo -e "${RED}⚠️  请修改 .env 文件中的 Redis 配置后再启动！${NC}"
        echo -e "${YELLOW}   vim $PROJECT_ROOT/.env${NC}"
        return 1
    fi
    
    start_backend
    BACKEND_STATUS=$?
    
    start_frontend
    FRONTEND_STATUS=$?
    
    # 总结
    echo -e "\n${GREEN}╔══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║         🎉 启动完成！                     ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
    
    echo -e "\n${CYAN}📌 访问地址：${NC}"
    [ $BACKEND_STATUS -eq 0 ] && echo -e "   后端 API: ${GREEN}http://localhost:${API_PORT}${NC}"
    [ $BACKEND_STATUS -eq 0 ] && echo -e "   API 文档: ${GREEN}http://localhost:${API_PORT}/docs${NC}"
    [ $FRONTEND_STATUS -eq 0 ] && echo -e "   前端界面: ${GREEN}http://localhost:${FRONTEND_PORT}${NC}"
    
    echo -e "\n${CYAN}📌 下一步操作：${NC}"
    echo -e "   1. 访问 Web 界面（上面的地址）"
    echo -e "   2. 点击 '爬虫控制' → '启动爬虫'"
    echo -e "   3. 等待几分钟，代理会自动抓取"
    
    echo -e "\n${CYAN}📌 管理命令：${NC}"
    echo -e "   查看状态: ${YELLOW}bash scripts/nb_ip.sh status${NC}"
    echo -e "   查看日志: ${YELLOW}bash scripts/nb_ip.sh logs${NC}"
    echo -e "   停止服务: ${YELLOW}bash scripts/nb_ip.sh stop${NC}"
    echo ""
}

# ==================== 停止函数 ====================

stop_all() {
    echo -e "${YELLOW}正在停止所有服务...${NC}\n"
    
    local stopped=0
    
    # 停止后端
    API_PID_FILE="$PID_DIR/api.pid"
    if [ -f "$API_PID_FILE" ]; then
        PID=$(cat "$API_PID_FILE")
        if kill -0 $PID 2>/dev/null; then
            kill $PID 2>/dev/null || true
            echo -e "${GREEN}✅ 后端 API 已停止 (PID: $PID)${NC}"
            stopped=$((stopped + 1))
        fi
        rm -f "$API_PID_FILE"
    fi
    
    # 停止前端
    FRONTEND_PID_FILE="$PID_DIR/frontend.pid"
    if [ -f "$FRONTEND_PID_FILE" ]; then
        PID=$(cat "$FRONTEND_PID_FILE")
        if kill -0 $PID 2>/dev/null; then
            kill $PID 2>/dev/null || true
            echo -e "${GREEN}✅ 前端服务已停止 (PID: $PID)${NC}"
            stopped=$((stopped + 1))
        fi
        rm -f "$FRONTEND_PID_FILE"
    fi
    
    if [ $stopped -eq 0 ]; then
        echo -e "${YELLOW}   没有运行中的服务${NC}"
    else
        echo -e "\n${GREEN}已停止 $stopped 个服务${NC}"
    fi
}

# ==================== 状态函数 ====================

show_status() {
    print_header
    load_env
    
    echo -e "${CYAN}📊 系统状态${NC}\n"
    
    # 后端状态
    API_PID_FILE="$PID_DIR/api.pid"
    if [ -f "$API_PID_FILE" ] && kill -0 $(cat "$API_PID_FILE") 2>/dev/null; then
        PID=$(cat "$API_PID_FILE")
        echo -e "${GREEN}✅ 后端 API${NC}"
        echo -e "   状态: 运行中"
        echo -e "   PID:  $PID"
        echo -e "   端口: ${API_PORT}"
        echo -e "   地址: http://localhost:${API_PORT}"
    else
        echo -e "${RED}⚫ 后端 API${NC}"
        echo -e "   状态: 未运行"
    fi
    
    echo ""
    
    # 前端状态
    FRONTEND_PID_FILE="$PID_DIR/frontend.pid"
    if [ -f "$FRONTEND_PID_FILE" ] && kill -0 $(cat "$FRONTEND_PID_FILE") 2>/dev/null; then
        PID=$(cat "$FRONTEND_PID_FILE")
        echo -e "${GREEN}✅ 前端服务${NC}"
        echo -e "   状态: 运行中"
        echo -e "   PID:  $PID"
        echo -e "   端口: ${FRONTEND_PORT}"
        echo -e "   地址: http://localhost:${FRONTEND_PORT}"
    else
        echo -e "${RED}⚫ 前端服务${NC}"
        echo -e "   状态: 未运行"
    fi
    
    echo ""
    
    # Redis 状态
    echo -e "${CYAN}🗄️  Redis 连接${NC}"
    if [ -n "$REDIS_HOST" ]; then
        echo -e "   地址: ${REDIS_HOST}:${REDIS_PORT}"
        echo -e "   数据库: ${REDIS_DB}"
        
        # 尝试连接测试
        if command -v redis-cli &> /dev/null; then
            if redis-cli -h ${REDIS_HOST} -p ${REDIS_PORT} -a ${REDIS_PASSWORD} -n ${REDIS_DB} PING &>/dev/null; then
                echo -e "   状态: ${GREEN}✅ 连接正常${NC}"
            else
                echo -e "   状态: ${RED}❌ 连接失败${NC}"
            fi
        elif command -v docker &> /dev/null; then
            # 尝试通过 docker
            if docker exec ts_server_redis redis-cli -a ${REDIS_PASSWORD} -n ${REDIS_DB} PING 2>&1 | grep -q PONG; then
                echo -e "   状态: ${GREEN}✅ 连接正常${NC}"
            else
                echo -e "   状态: ${RED}❌ 连接失败${NC}"
            fi
        fi
    else
        echo -e "   ${YELLOW}未配置${NC}"
    fi
    
    echo ""
}

# ==================== 日志函数 ====================

show_logs() {
    local log_type=${1:-api}
    local lines=${2:-50}
    
    case $log_type in
        api|backend)
            LOG_FILE="$LOG_DIR/api.log"
            TITLE="后端 API"
            ;;
        frontend|web)
            LOG_FILE="$LOG_DIR/frontend.log"
            TITLE="前端服务"
            ;;
        spider|crawler)
            LOG_FILE="$HOME/pythonlogs/proxy_check.log"
            TITLE="爬虫日志"
            ;;
        error)
            LOG_FILE="$HOME/pythonlogs/proxy_error.log"
            TITLE="错误日志"
            ;;
        *)
            echo -e "${RED}❌ 未知的日志类型: $log_type${NC}"
            echo -e "${YELLOW}   可用类型: api, frontend, spider, error${NC}"
            return 1
            ;;
    esac
    
    echo -e "${CYAN}📄 ${TITLE} 日志（最近 ${lines} 行）${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if [ -f "$LOG_FILE" ]; then
        tail -n $lines "$LOG_FILE"
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${CYAN}日志文件: $LOG_FILE${NC}"
    else
        echo -e "${RED}❌ 日志文件不存在: $LOG_FILE${NC}"
    fi
}

# ==================== 下载 GeoIP ====================

download_geoip() {
    print_header
    echo -e "${GREEN}正在下载 GeoIP 数据库...${NC}\n"
    
    DATA_DIR="$PROJECT_ROOT/data"
    MMDB_FILE="$DATA_DIR/GeoLite2-City.mmdb"
    
    mkdir -p "$DATA_DIR"
    
    # 检查是否已存在
    if [ -f "$MMDB_FILE" ]; then
        echo -e "${YELLOW}⚠️  数据库文件已存在: $MMDB_FILE${NC}"
        read -p "是否重新下载？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${GREEN}✅ 使用现有数据库${NC}"
            return 0
        fi
    fi
    
    # 下载地址（使用 GitHub 镜像）
    DOWNLOAD_URL="https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-City.mmdb"
    
    echo "下载地址: $DOWNLOAD_URL"
    echo ""
    
    if command -v wget &> /dev/null; then
        wget -O "$MMDB_FILE" "$DOWNLOAD_URL" --progress=bar:force 2>&1
    elif command -v curl &> /dev/null; then
        curl -L -o "$MMDB_FILE" "$DOWNLOAD_URL" --progress-bar
    else
        echo -e "${RED}❌ 错误：未找到 wget 或 curl 命令${NC}"
        echo -e "\n${YELLOW}请手动下载：${NC}"
        echo "1. 访问: https://dev.maxmind.com/geoip/geolite2-free-geolocation-data"
        echo "2. 注册免费账号"
        echo "3. 下载 GeoLite2-City.mmdb"
        echo "4. 放到: $DATA_DIR/"
        return 1
    fi
    
    # 检查下载结果
    if [ -f "$MMDB_FILE" ] && [ -s "$MMDB_FILE" ]; then
        FILE_SIZE=$(du -h "$MMDB_FILE" | cut -f1)
        echo -e "\n${GREEN}✅ 下载成功！${NC}"
        echo -e "   文件大小: $FILE_SIZE"
        echo -e "   保存路径: $MMDB_FILE"
        echo -e "\n${GREEN}=== GeoIP 功能已启用 ===${NC}"
        echo "您现在可以享受 < 1ms 的超快地理位置查询！"
    else
        echo -e "\n${RED}❌ 下载失败！${NC}"
        echo -e "${YELLOW}系统将自动降级到在线 API（速度较慢）${NC}"
        return 1
    fi
}

# ==================== 帮助函数 ====================

show_help() {
    print_header
    
    echo -e "${CYAN}用法：${NC}"
    echo -e "  bash scripts/nb_ip.sh [命令] [参数]"
    echo ""
    
    echo -e "${CYAN}可用命令：${NC}\n"
    
    echo -e "${GREEN}  start${NC}"
    echo -e "    启动所有服务（后端 API + 前端界面）"
    echo -e "    示例: bash scripts/nb_ip.sh start"
    echo ""
    
    echo -e "${GREEN}  stop${NC}"
    echo -e "    停止所有服务"
    echo -e "    示例: bash scripts/nb_ip.sh stop"
    echo ""
    
    echo -e "${GREEN}  restart${NC}"
    echo -e "    重启所有服务（先停止再启动）"
    echo -e "    示例: bash scripts/nb_ip.sh restart"
    echo ""
    
    echo -e "${GREEN}  status${NC}"
    echo -e "    查看系统运行状态"
    echo -e "    显示: 服务状态、PID、端口、Redis 连接状态"
    echo -e "    示例: bash scripts/nb_ip.sh status"
    echo ""
    
    echo -e "${GREEN}  logs [类型] [行数]${NC}"
    echo -e "    查看日志文件"
    echo -e "    参数:"
    echo -e "      类型: api|frontend|spider|error (默认: api)"
    echo -e "      行数: 显示最后 N 行 (默认: 50)"
    echo -e "    示例:"
    echo -e "      bash scripts/nb_ip.sh logs           # 查看后端日志（50行）"
    echo -e "      bash scripts/nb_ip.sh logs api 100   # 查看后端日志（100行）"
    echo -e "      bash scripts/nb_ip.sh logs spider    # 查看爬虫日志"
    echo -e "      bash scripts/nb_ip.sh logs frontend  # 查看前端日志"
    echo ""
    
    echo -e "${GREEN}  download${NC}"
    echo -e "    下载 GeoIP 地理位置数据库（可选，提升性能 100 倍）"
    echo -e "    文件大小: ~30MB"
    echo -e "    性能提升: 查询速度从 100-500ms 降至 < 1ms"
    echo -e "    示例: bash scripts/nb_ip.sh download"
    echo ""
    
    echo -e "${GREEN}  help${NC}"
    echo -e "    显示此帮助信息"
    echo -e "    示例: bash scripts/nb_ip.sh help"
    echo ""
    
    echo -e "${CYAN}配置说明：${NC}\n"
    
    echo -e "${YELLOW}  .env 文件配置项：${NC}"
    echo ""
    echo -e "  ${GREEN}后端端口：${NC}"
    echo -e "    API_PORT=8000              # 后端 API 服务端口"
    echo ""
    echo -e "  ${GREEN}前端端口：${NC}"
    echo -e "    FRONTEND_PORT=5173         # 前端界面端口"
    echo ""
    echo -e "  ${GREEN}API 访问密钥（Token）：${NC}"
    echo -e "    API_KEYS=key1,key2         # 对外 API 的访问密钥"
    echo -e "                               # 多个密钥用逗号分隔"
    echo -e "                               # 其他程序调用时需要提供此密钥"
    echo ""
    echo -e "  ${GREEN}Redis 配置：${NC}"
    echo -e "    REDIS_HOST=127.0.0.1       # Redis 服务器地址"
    echo -e "    REDIS_PORT=6379            # Redis 端口"
    echo -e "    REDIS_PASSWORD=***         # Redis 密码"
    echo -e "    REDIS_DB=0                 # 使用的数据库编号（0-15）"
    echo ""
    
    echo -e "${CYAN}API Token 使用示例：${NC}\n"
    echo -e "  ${YELLOW}# 获取随机代理${NC}"
    echo -e "  curl -H \"X-API-Key: demo_key_12345\" \\"
    echo -e "    http://localhost:8000/api/public/proxy/random"
    echo ""
    echo -e "  ${YELLOW}# 获取中国代理${NC}"
    echo -e "  curl -H \"X-API-Key: demo_key_12345\" \\"
    echo -e "    \"http://localhost:8000/api/public/proxy/list?country=CN&size=10\""
    echo ""
    
    echo -e "${CYAN}更多信息：${NC}"
    echo -e "  文档: cat README.md"
    echo -e "  更新日志: cat docs/CHANGELOG.md"
    echo -e "  配置模板: cat env.example"
    echo ""
}

# ==================== 主函数 ====================

main() {
    local command=${1:-help}
    
    case $command in
        start)
            start_all
            ;;
        stop)
            stop_all
            ;;
        restart)
            echo -e "${CYAN}重启服务...${NC}\n"
            stop_all
            sleep 2
            start_all
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs ${2:-api} ${3:-50}
            ;;
        download)
            download_geoip
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}❌ 未知命令: $command${NC}"
            echo -e "${YELLOW}使用 'bash scripts/nb_ip.sh help' 查看帮助${NC}"
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"

