# 更新日志

## v2.0.0 (2025-10-22) - 完全重构版本

### 🎉 重大更新

#### 项目管理
- ✨ 采用 **uv** 作为 Python 包管理器，依赖安装速度提升 10 倍
- ✨ 引入 **pydantic-settings** 实现 `.env` 配置文件支持
- ✨ 重构项目结构，符合现代 Python 项目标准
- ✨ 清理旧文件，代码组织更清晰

#### 后端架构
- ✨ 完全重写为 **FastAPI** 应用，性能大幅提升
- ✨ 实现三大 API 模块：
  - `public` - 对外公开 API（需 API Key 认证）
  - `admin` - 内部管理 API（代理管理、统计）
  - `spider` - 爬虫控制 API（启动/停止/日志）
- ✨ 自动生成 **OpenAPI 文档**（Swagger UI）
- ✨ 完善的数据验证和错误处理

#### GeoIP 地理位置识别（新增）
- ✨ **混合策略**：本地 GeoIP2 数据库（< 1ms）+ ip-api.com 在线 API（备份）
- ✨ 支持 **60+ 国家**中文名称映射
- ✨ 自动生成**国旗 emoji**（🇨🇳 🇺🇸 🇯🇵 等）
- ✨ **Redis 缓存**查询结果（7 天）
- ✨ 性能对比：本地查询比在线 API 快 **100-500 倍**

#### 代理检测增强
- ✨ 集成 GeoIP，自动识别代理所属国家/地区
- ✨ 记录**生命周期信息**：
  - 创建时间、最后检测时间
  - 检测次数、成功次数、失败次数
  - 平均响应时间
- ✨ 代理详细信息存储（Redis Hash）
- ✨ 支持按**国家筛选**代理

#### 爬虫管理器（新增）
- ✨ **多进程管理**：独立进程运行爬虫，不阻塞主服务
- ✨ **Web 端控制**：通过界面或 API 启动/停止爬虫
- ✨ **状态监控**：实时查看运行状态、PID、运行时长
- ✨ **日志查看**：Web 端实时查看运行日志
- ✨ **站点配置**：可配置启用的代理站点

#### 前端界面（全新）
- ✨ 基于 **Vue 3 + Vite + Element Plus**
- ✨ 三个核心页面：
  - **仪表盘**：统计概览、国家分布
  - **代理管理**：列表、搜索、筛选、测试、删除
  - **爬虫控制**：启动/停止、站点状态、日志查看
- ✨ 左侧导航栏布局，参考现代管理后台设计
- ✨ 实时数据刷新
- ✨ 国旗 emoji 显示
- ✨ 响应式设计

#### 辅助工具
- ✨ **一键启动脚本**：`bash scripts/start.sh`
- ✨ **一键停止脚本**：`bash scripts/stop.sh`
- ✨ **GeoIP 下载脚本**：`bash scripts/download_geoip.sh`
- ✨ **配置模板**：`env.example`

#### 文档完善
- ✨ 全新的 **README.md**：详细的安装和使用说明
- ✨ **重构方案文档**：完整的技术设计和实施步骤
- ✨ **API 文档**：自动生成的 Swagger 文档
- ✨ **更新日志**：本文件

---

### 📊 统计数据

- **提交次数**：9 次
- **文件变更**：47 个文件
- **代码新增**：9,050+ 行
- **代码删除**：693 行
- **净增加**：8,357 行

---

### 🔄 迁移指南

#### 从 v1.0 升级到 v2.0

**1. 备份数据**
```bash
# 备份 Redis 数据
redis-cli SAVE
```

**2. 拉取新代码**
```bash
git pull origin main
```

**3. 安装 uv**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

**4. 安装依赖**
```bash
uv sync
cd frontend && npm install
```

**5. 配置环境变量**
```bash
cp env.example .env
vim .env  # 修改 Redis 配置
```

**6. 启动服务**
```bash
bash scripts/start.sh
```

---

### ⚠️ 破坏性变更

#### 1. 配置方式改变
- **旧版本**：修改 `proxy_pool_config.py`
- **新版本**：修改 `.env` 文件

#### 2. 启动方式改变
- **旧版本**：`python run_proxy.py`
- **新版本**：`bash scripts/start.sh` 或 Web 界面启动

#### 3. 目录结构改变
- 所有 Python 代码移至 `backend/` 目录
- 旧文件移至 `old/` 目录（本地备份）

#### 4. API 接口改变
- **新增**：对外公开 API（需 API Key）
- **新增**：管理员 API
- **新增**：爬虫控制 API

---

### 🐛 已知问题

暂无

---

### 📝 待办事项

- [ ] 添加单元测试
- [ ] 添加 Docker 支持
- [ ] 添加代理质量评分系统
- [ ] 添加代理池使用统计
- [ ] 支持更多代理站点
- [ ] 添加 Telegram Bot 通知

---

### 🙏 致谢

- [funboost](https://github.com/ydf0509/funboost) - 分布式任务框架
- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Python Web 框架
- [Vue.js](https://vuejs.org/) - 渐进式前端框架
- [Element Plus](https://element-plus.org/) - Vue 3 组件库
- [MaxMind GeoLite2](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data) - 免费 GeoIP 数据库

---

## v1.0.0 (之前版本)

### 功能
- ✅ 基础代理池功能
- ✅ 多站点代理抓取
- ✅ 代理有效性检测
- ✅ Redis 存储
- ✅ funboost 任务调度

