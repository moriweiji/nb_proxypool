#!/bin/bash
# GeoIP 数据库下载脚本
#
# MaxMind GeoLite2 数据库下载说明：
# 1. 免费版本：GeoLite2（需要注册账号）
# 2. 数据更新：每月第一个星期二
# 3. 文件大小：~30MB（City版本），~6MB（Country版本）
#
# 使用方法：
#   bash scripts/download_geoip.sh

set -e  # 遇到错误立即退出

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_ROOT/data"
MMDB_FILE="$DATA_DIR/GeoLite2-City.mmdb"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== GeoIP 数据库下载工具 ===${NC}\n"

# 创建数据目录
mkdir -p "$DATA_DIR"

# 检查是否已存在
if [ -f "$MMDB_FILE" ]; then
    echo -e "${YELLOW}⚠️  数据库文件已存在: $MMDB_FILE${NC}"
    read -p "是否重新下载？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}✅ 使用现有数据库${NC}"
        exit 0
    fi
fi

# 方式 1：使用 MaxMind 镜像（推荐）
echo -e "${GREEN}正在下载 GeoLite2-City 数据库...${NC}"
echo "提示：如果下载失败，请访问 https://dev.maxmind.com/geoip/geolite2-free-geolocation-data"
echo "      注册账号后手动下载 GeoLite2-City.mmdb 文件到 $DATA_DIR"
echo ""

# 临时下载地址（使用第三方镜像，不保证长期可用）
# 注意：MaxMind 现在要求注册才能下载，这里提供备选方案

# 方案 A：使用公开镜像（可能不可用）
DOWNLOAD_URL="https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-City.mmdb"

echo "正在从镜像下载: $DOWNLOAD_URL"

if command -v wget &> /dev/null; then
    wget -O "$MMDB_FILE" "$DOWNLOAD_URL" 2>&1 | grep --line-buffered "%" | \
        sed -u -e "s/[^0-9]*\([0-9]*\)%.*/\1/" | \
        while read pct; do
            echo -ne "${GREEN}下载进度: $pct%\r${NC}"
        done
    echo ""
elif command -v curl &> /dev/null; then
    curl -L -o "$MMDB_FILE" "$DOWNLOAD_URL" --progress-bar
else
    echo -e "${RED}❌ 错误：未找到 wget 或 curl 命令${NC}"
    echo "请手动下载 GeoLite2-City.mmdb 到 $DATA_DIR"
    exit 1
fi

# 检查下载结果
if [ -f "$MMDB_FILE" ] && [ -s "$MMDB_FILE" ]; then
    FILE_SIZE=$(du -h "$MMDB_FILE" | cut -f1)
    echo -e "${GREEN}✅ 下载成功！${NC}"
    echo -e "   文件大小: $FILE_SIZE"
    echo -e "   保存路径: $MMDB_FILE"
    echo ""
    echo -e "${GREEN}=== 安装完成 ===${NC}"
    echo "您现在可以启动项目，GeoIP 功能将自动启用。"
else
    echo -e "${RED}❌ 下载失败！${NC}"
    echo ""
    echo -e "${YELLOW}请手动下载：${NC}"
    echo "1. 访问：https://dev.maxmind.com/geoip/geolite2-free-geolocation-data"
    echo "2. 注册免费账号"
    echo "3. 下载 GeoLite2-City.mmdb"
    echo "4. 将文件放到：$DATA_DIR/"
    exit 1
fi

# 设置定期更新提示
echo ""
echo -e "${YELLOW}💡 提示：GeoIP 数据库每月更新一次${NC}"
echo "   建议设置定时任务自动更新："
echo "   crontab -e"
echo "   0 0 1 * * $SCRIPT_DIR/download_geoip.sh"

