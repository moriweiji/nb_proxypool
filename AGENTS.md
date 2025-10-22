# Repository Guidelines

## 项目结构与模块组织
- `backend/`：FastAPI 后端。`api/` 路由，`core/` 配置与调度（Redis、funboost），`crawlers/` 站点抓取，`schemas/` Pydantic 模型，`utils/` 工具，`main.py` 入口。
- `frontend/`：Vue 3 + Vite 前端（`src/`、`views/`、`router/`）。
- `scripts/`：运维脚本（`nb_ip.sh`、`download_geoip.sh`）。
- `tests/`：测试用例；`docs/` 文档；`data/` 数据文件；`.env` 见 `env.example`。

## 构建、测试与开发命令
- 一键启动（后端+前端）：`bash scripts/nb_ip.sh start`
- 后端开发：`uv run uvicorn backend.main:app --reload`
- 前端开发：`cd frontend && npm run dev`
- 运行测试：`uv run pytest`
- 代码检查/格式化：`ruff check . --fix && black .`

## 代码风格与命名约定
- Python：4 空格缩进，Black/Ruff，行宽 120（见 `pyproject.toml`）。
- 命名：模块/文件 lower_snake_case；函数/变量 lower_snake_case；类 PascalCase；常量 UPPER_SNAKE_CASE。
- 类型：优先添加 type hints；公共函数附简短 docstring。
- 配置：使用 `.env`（勿提交），参考 `env.example`；敏感值仅放环境变量。

## 测试规范
- 框架：pytest + pytest-asyncio。
- 位置与命名：`tests/test_*.py`；异步用例标注 `@pytest.mark.asyncio`。
- 覆盖建议：总体 ≥80%，核心模块（`backend/api`、`backend/core`、`backend/crawlers`）必须有用例。
- 本地运行：`uv run pytest -q`；可补充集成测试调用实际 API 路由。

## 提交与 Pull Request
- 提交信息：采用 Conventional Commits。
  - 示例：`feat(api): add /proxy/list country filter`；`fix(core): handle Redis auth error`。
- PR 要求：变更摘要、影响范围、测试结果/命令、关联 Issue、UI 变更附截图。
- 检查清单：通过 `ruff`/`black`/`pytest`；不提交 `.env`、`data/GeoLite2-City.mmdb`、生成文件。

## 安全与配置
- 禁止在仓库中暴露密钥/API Key；仅用 `.env` 管理。
- 生产环境限制 CORS 来源；Redis 必须开启鉴权。
- GeoIP 库放在 `data/`；需要时运行 `bash scripts/nb_ip.sh download` 下载。
