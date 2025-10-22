# nb_proxypool 2.0

> 高性能代理池系统 - 基于 FastAPI + Vue 3 + funboost

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Vue](https://img.shields.io/badge/Vue-3.4+-brightgreen.svg)](https://vuejs.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ 特性

### 核心功能
- 🌐 **多站点爬取**：支持 16+ 免费代理网站自动抓取
- ⚡ **高速检测**：QPS 100，并发 300-400，秒级验证代理有效性
- 🗺️ **地理位置**：自动识别代理 IP 所属国家/地区（60+ 国家）
- 🚀 **高性能**：Redis 存储，funboost 分布式任务调度
- 📊 **可视化管理**：Vue 3 + Element Plus 现代化 Web 界面
- 🔌 **RESTful API**：对外提供代理获取接口（支持 API Key 认证）

### 技术亮点
- ✅ **uv 项目管理**：快速依赖安装和虚拟环境管理
- ✅ **.env 配置**：灵活的环境变量配置
- ✅ **GeoIP 混合策略**：本地数据库（< 1ms）+ 在线 API 备份
- ✅ **生命周期监控**：记录代理创建、检测、质量等详细信息
- ✅ **Web 端爬虫控制**：启动/停止/查看日志，无需命令行
- ✅ **国家筛选**：按国家代码获取指定地区代理

---

## 📦 快速开始

### 1. 环境要求

```bash
# 必须
- Python 3.8+
- Redis
- Node.js 16+ (前端)

# 推荐
- uv (Python 包管理器)
```

### 2. 安装 uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

### 3. 克隆项目

```bash
git clone https://github.com/moriweiji/nb_proxypool.git
cd nb_proxypool
```

### 4. 配置环境变量

```bash
# 复制配置文件
cp env.example .env

# 编辑配置（重要！）
vim .env

# 必须配置的项：
# - REDIS_HOST：Redis 地址
# - REDIS_PORT：Redis 端口
# - REDIS_PASSWORD：Redis 密码（如有）
```

### 5. 一键启动

```bash
bash scripts/start.sh
```

访问：
- **Web 管理界面**：http://localhost:5173
- **API 文档**：http://localhost:8000/docs
- **健康检查**：http://localhost:8000/health

---

## 🎯 使用说明

### Web 管理界面

#### 1. 仪表盘
- 查看代理总数、有效数
- 查看爬虫运行状态
- 查看国家分布统计

#### 2. 代理管理
- 浏览所有代理（支持分页）
- 按国家筛选（🇨🇳 🇺🇸 🇯🇵 等）
- 搜索 IP 或城市
- 测试代理有效性
- 删除无效代理

#### 3. 爬虫控制
- ▶️ 启动爬虫
- ⏸️ 停止爬虫
- 查看运行状态（PID、运行时长）
- 查看各站点配置
- 实时查看运行日志

---

### 对外 API 使用

#### 获取随机代理

```bash
# 需要 API Key
curl -H "X-API-Key: demo_key_12345" \
  http://localhost:8000/api/public/proxy/random

# 响应示例
{
  "http": "http://1.2.3.4:8080",
  "https": "http://1.2.3.4:8080",
  "ip": "1.2.3.4",
  "country": "CN",
  "country_name": "中国",
  "flag": "🇨🇳",
  "platform": "kuaidaili"
}
```

#### 批量获取代理

```bash
# 获取 20 个代理
curl -H "X-API-Key: demo_key_12345" \
  "http://localhost:8000/api/public/proxy/list?size=20"

# 按国家筛选
curl -H "X-API-Key: demo_key_12345" \
  "http://localhost:8000/api/public/proxy/list?country=US&size=10"
```

#### 查看可用国家

```bash
curl -H "X-API-Key: demo_key_12345" \
  http://localhost:8000/api/public/countries
```

---

## 🔧 配置说明

### Redis 配置

```bash
# .env 文件
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=your_password
REDIS_DB=0
```

### 代理池配置

```bash
# 代理检测超时（秒）
PROXY_TIMEOUT=5

# 代理检测 URL
PROXY_CHECK_URL=https://www.baidu.com/

# QPS 和并发数
CHECK_NEW_PROXY_QPS=100
CHECK_NEW_PROXY_CONCURRENT=300
```

### 爬虫配置

```bash
# 启用的代理站点（逗号分隔）
ENABLED_SITES=Kuaidaili,Xici,Ip89,Ihuan,Zdaye,Beesproxy

# 每个站点抓取的最大页数
MAX_CRAWL_PAGES=4

# 定时任务间隔（秒）
SPIDER_INTERVAL=30
```

### API 配置

```bash
# API Key（多个用逗号分隔）
API_KEYS=your_api_key_1,your_api_key_2
```

---

## 🌐 GeoIP 配置

### 下载 GeoIP 数据库（可选，提升性能）

```bash
# 自动下载
bash scripts/download_geoip.sh

# 手动下载
# 1. 访问：https://dev.maxmind.com/geoip/geolite2-free-geolocation-data
# 2. 注册免费账号
# 3. 下载 GeoLite2-City.mmdb
# 4. 放到 data/ 目录
```

**性能对比**：

| 方案 | 查询速度 | 准确率 | 限制 |
|------|---------|--------|------|
| 本地 GeoIP | < 1ms | 99%+ | 无 |
| ip-api.com（备用）| 100-500ms | 99.9% | 45次/分钟 |

---

## 📊 支持的代理站点

| 站点 | 质量 | 分页 | 说明 |
|------|------|------|------|
| Kuaidaili | ⭐⭐⭐⭐ | ✅ | 快代理，质量较好 |
| Xici | ⭐⭐⭐ | ❌ | 西刺代理 |
| Ip89 | ⭐⭐⭐⭐ | ✅ | 89免费代理 |
| Ihuan | ⭐⭐⭐⭐ | ✅ | 小幻代理 |
| Zdaye | ⭐⭐⭐ | ❌ | 站大爷 |
| Beesproxy | ⭐⭐⭐⭐ | ✅ | Bees Proxy |
| Kaixin | ⭐⭐⭐ | ✅ | 开心代理 |

---

## 🛠️ 开发指南

### 项目结构

```
nb_proxypool/
├── backend/                 # 后端代码
│   ├── api/                # API 路由
│   │   ├── public.py       # 对外 API
│   │   ├── admin.py        # 管理 API
│   │   └── spider.py       # 爬虫控制 API
│   ├── core/               # 核心逻辑
│   │   ├── settings.py     # 配置管理
│   │   ├── config.py       # Redis 配置
│   │   ├── checker.py      # 代理检测
│   │   ├── client.py       # 代理客户端
│   │   └── spider_manager.py  # 爬虫管理器
│   ├── crawlers/           # 爬虫
│   │   └── sites.py        # 各站点爬虫
│   ├── schemas/            # 数据模型
│   ├── utils/              # 工具
│   │   ├── geoip.py        # 地理位置识别
│   │   └── auth.py         # API 认证
│   └── main.py             # FastAPI 应用入口
├── frontend/               # 前端代码
│   └── src/
│       ├── views/          # 页面
│       ├── api/            # API 封装
│       └── router/         # 路由
├── scripts/                # 脚本
│   ├── start.sh            # 启动脚本
│   ├── stop.sh             # 停止脚本
│   └── download_geoip.sh   # GeoIP 下载
├── docs/                   # 文档
├── data/                   # 数据文件
├── .env                    # 配置文件
└── pyproject.toml          # 项目配置
```

### 本地开发

```bash
# 后端开发
uv run uvicorn backend.main:app --reload

# 前端开发
cd frontend
npm run dev

# 运行测试
uv run pytest
```

---

## 📝 常见问题

### 1. Redis 连接失败

检查 `.env` 文件中的 Redis 配置是否正确，确保 Redis 服务已启动。

### 2. 代理池为空

首次使用需要启动爬虫：

- 方式 1：Web 界面 → 爬虫控制 → 启动爬虫
- 方式 2：调用 API：`POST http://localhost:8000/api/spider/start`

### 3. GeoIP 查询失败

如果未下载 GeoIP 数据库，会自动降级到在线 API（ip-api.com），速度较慢但可用。

### 4. 前端无法访问

确保后端 API 已启动（http://localhost:8000），检查浏览器控制台是否有 CORS 错误。

---

## 🔄 更新日志

### v2.0.0 (2025-10-22)

- ✨ 完全重构，采用 uv 项目管理
- ✨ 新增 FastAPI 后端 + Vue 3 前端
- ✨ 新增 GeoIP 地理位置识别
- ✨ 新增 Web 管理界面
- ✨ 新增 .env 配置支持
- ✨ 新增生命周期监控
- ✨ 新增国家筛选功能
- ✨ 新增对外 API 接口
- ✨ 新增爬虫 Web 端控制

### v1.0.0

- 基础代理池功能

---

## 📄 许可证

MIT License

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## ⭐ Star History

如果这个项目对你有帮助，欢迎 Star ⭐

---

## 📧 联系方式

- GitHub: [@moriweiji](https://github.com/moriweiji)
- Project: [nb_proxypool](https://github.com/moriweiji/nb_proxypool)
