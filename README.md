# 📝 DevDiary - 开发者的第二大脑

[English](#english) | [中文](#中文)

---

<a id="中文"></a>

## 🌟 简介

DevDiary 是一个面向开发者的智能日记工具，通过分析 Git 提交历史，借助 AI 自动生成开发日记、周报和月报。帮助你记录、理解和反思编程生活。

## ✨ 核心功能

- 🔍 **Git 智能扫描** — 自动分析 commit 历史，理解代码变更意图
- 🤖 **AI 内容生成** — 支持 OpenAI / DeepSeek / 智谱 GLM / 工蜂 AI，通过 Provider 抽象可轻松扩展
- 📄 **多种文体** — 日记体、技术博客体、周报体，随心切换
- 📅 **自定义日期** — 支持自选日期范围，灵活生成任意时段的日记
- 💻 **CLI 工具** — 命令行一键生成，集成到你的工作流
- 🌐 **Web Dashboard** — 精美的响应式 Web 界面，可视化展示你的编程轨迹
- 📊 **真实数据统计** — 提交趋势图、编码时间热力图、语言分布、项目活跃度，全部基于真实 Git 数据
- 💡 **智能洞察** — 自动分析最活跃时段、最活跃项目、连续编码天数等
- 🏆 **年度开发者报告** — 类似 GitHub Wrapped / Spotify Wrapped，全面回顾你的年度编码轨迹
- 🔍 **Git 实时监听** — 后台自动监听仓库变更，定时/推送触发自动生成日记

## 📸 页面一览

| 页面 | 说明 |
|------|------|
| 🏠 仪表盘 | 总览提交数、日记数、项目数，快速生成日记 |
| 📋 日记列表 | 浏览、搜索、管理所有日记 |
| 📖 日记详情 | Markdown 渲染的日记内容，支持代码高亮 |
| 📁 项目管理 | 管理 Git 仓库，查看项目统计 |
| 📊 统计概览 | 提交趋势图、编码热力图、语言分布、智能洞察 |
| 🏆 年度报告 | 年度总结、月度趋势、项目排行、语言分布、成就系统 |
| 🔍 Git 监听 | 服务状态管理、调度配置、通知设置 |

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+（前端开发）
- Git

### 安装

```bash
# 克隆项目
git clone <repo-url>
cd DevDiary

# 安装后端依赖
pip install -e .

# 安装前端依赖
cd frontend
npm install
cd ..
```

### 初始化

```bash
devdiary init
```

按提示配置 AI 后端（OpenAI / DeepSeek / 智谱 / 工蜂）和仓库路径。

### 生成日记

```bash
# 生成今日日记
devdiary today

# 生成本周周报
devdiary week

# 生成月报
devdiary month

# 自定义日期范围
devdiary generate --from 2026-03-01 --to 2026-03-07

# 年度开发者报告
devdiary report
devdiary report --year 2025

# Git 实时监听
devdiary watch             # 查看状态
devdiary watch --start     # 启动后台监听
devdiary watch --stop      # 停止监听
```

### 启动 Web 服务

```bash
# 启动后端 API
uvicorn src.devdiary.api.app:app --reload --port 8000

# 启动前端开发服务器（另一个终端）
cd frontend
npm run dev
```

访问 http://localhost:3000 查看 Dashboard。

> 💡 **生产部署**：构建前端 (`npm run build`) 后，后端会自动托管 `frontend/dist` 静态文件，只需启动后端即可通过 http://localhost:8000 访问完整应用。

## ⚙️ 配置

配置文件位于项目根目录的 `.devdiary/config.yaml`：

```yaml
ai:
  provider: openai          # openai / deepseek / zhipu / gongfeng
  api_key: your-api-key
  model: gpt-4o-mini        # 或 deepseek-chat / glm-4-flash 等
  base_url: null            # 自定义 API 地址（DeepSeek: https://api.deepseek.com）

repos:
  - path: /path/to/your/repo
    name: my-project

output:
  dir: ./diaries
  format: markdown          # markdown / html / both
  style: diary              # diary / blog / report
```

### 支持的 AI Provider

| Provider | 模型示例 | base_url |
|----------|---------|----------|
| OpenAI | `gpt-4o-mini`, `gpt-4o` | 默认 |
| DeepSeek | `deepseek-chat`, `deepseek-reasoner` | `https://api.deepseek.com` |
| 智谱 GLM | `glm-4-flash`, `glm-4` | 默认 |
| 工蜂 AI | — | 内部地址 |

### Git 监听配置

监听服务的配置文件位于 `.devdiary/watch.yaml`：

```yaml
enabled: true
schedule: daily          # daily / weekly / on_push
time: "09:00"            # 每日/每周执行时间 (HH:MM)
weekday: monday          # weekly 模式下的执行日
auto_scan: true
notify:
  desktop: true          # 桌面通知
  email: null            # 邮箱通知（留空则不发送）
  webhook: null          # 飞书/钉钉/Slack Webhook URL
```

调度模式说明：
- **daily** — 每天指定时间自动扫描并生成日记
- **weekly** — 每周指定日期和时间生成周报
- **on_push** — 每 5 分钟检查一次，发现新提交立即生成

## 🔗 API 文档

启动后端后访问：

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### 主要 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/diaries/` | 获取日记列表 |
| `POST` | `/api/diaries/generate` | AI 生成日记 |
| `GET` | `/api/diaries/{id}` | 获取日记详情 |
| `GET` | `/api/projects/` | 获取项目列表 |
| `POST` | `/api/projects/` | 添加项目 |
| `GET` | `/api/projects/overview` | 项目统计概览 |
| `GET` | `/api/stats/commit-trend` | 每日提交趋势 |
| `GET` | `/api/stats/heatmap` | 编码时间热力图 |
| `GET` | `/api/stats/insights` | 智能数据洞察 |
| `GET` | `/api/report` | 年度开发者报告 |
| `GET` | `/api/watcher/status` | 获取 Watcher 状态 |
| `POST` | `/api/watcher/start` | 启动 Watcher |
| `POST` | `/api/watcher/stop` | 停止 Watcher |
| `GET` | `/api/watcher/config` | 获取监听配置 |
| `PUT` | `/api/watcher/config` | 更新监听配置 |
| `GET` | `/api/health` | 健康检查 |

## 🛠️ 技术栈

| 模块 | 技术 |
|------|------|
| 后端 | Python 3.11+ / FastAPI / SQLAlchemy 2.0 (async) / Pydantic V2 |
| 前端 | Vue 3 / TypeScript / Vite / Naive UI / TailwindCSS / Pinia / ECharts |
| CLI | Click / Rich |
| AI | OpenAI / DeepSeek / 智谱 GLM / 工蜂 AI（Provider 抽象，可扩展） |
| 数据库 | SQLite（本地）/ PostgreSQL（团队版） |
| 数据库迁移 | Alembic |

## 📁 项目结构

```
DevDiary/
├── src/devdiary/              # Python 后端源码
│   ├── api/                   # FastAPI Web API
│   │   ├── routes/            # 路由模块
│   │   │   ├── diaries.py     # 日记 CRUD + AI 生成
│   │   │   ├── projects.py    # 项目管理
│   │   │   ├── stats.py       # 统计聚合 API
│   │   │   ├── report.py      # 年度开发者报告 API
│   │   │   └── watcher.py     # Git 监听管理 API
│   │   ├── app.py             # 应用工厂
│   │   └── schemas.py         # Pydantic 数据模型
│   ├── scanner/               # Git 扫描引擎
│   ├── analyzer/              # 数据分析
│   ├── generator/             # AI 内容生成（Provider 抽象）
│   ├── renderer/              # 输出渲染（Markdown/HTML）
│   ├── cli/                   # CLI 工具
│   ├── watcher.py             # Git 实时监听服务
│   ├── models.py              # SQLAlchemy ORM 模型
│   ├── database.py            # 数据库连接管理
│   └── config.py              # 配置加载
├── frontend/                  # Vue 3 前端
│   └── src/
│       ├── views/             # 页面组件
│       │   ├── HomeView.vue       # 仪表盘
│       │   ├── DiaryListView.vue  # 日记列表
│       │   ├── DiaryDetailView.vue# 日记详情
│       │   ├── ProjectsView.vue   # 项目管理
│       │   ├── StatsView.vue      # 统计概览
│       │   ├── AnnualReportView.vue # 年度报告
│       │   └── WatcherView.vue    # Git 监听管理
│       ├── components/        # 通用组件
│       │   ├── AppLayout.vue      # 响应式布局
│       │   ├── GenerateDialog.vue # 日记生成对话框
│       │   ├── DiaryCard.vue      # 日记卡片
│       │   ├── MarkdownViewer.vue # Markdown 渲染
│       │   └── StatsChart.vue     # 图表封装
│       ├── api/               # API 请求封装
│       └── types/             # TypeScript 类型定义
├── tests/                     # 测试用例（42+ tests）
├── alembic/                   # 数据库迁移
└── pyproject.toml             # 项目配置
```

## 🧑‍💻 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 运行测试（带覆盖率）
pytest --cov=devdiary

# 代码格式化
black src/ tests/

# 类型检查
mypy src/

# 前端开发
cd frontend
npm run dev          # 开发服务器
npm run build        # 生产构建
```

## 📋 版本历史

### V0.4 — 年度报告 & Git 实时监听
- 🏆 **年度开发者报告** — 类似 GitHub Wrapped，年度总结、月度趋势、项目排行榜、语言分布、成就系统
- 🔍 **Git 实时监听** — 后台 Watcher 服务，支持每天/每周/推送后三种调度模式，自动扫描仓库生成日记
- 📡 **Watcher 管理面板** — 启动/停止、状态监控、调度配置、通知设置（桌面/邮箱/Webhook）
- 📊 **4 个可视化图表** — 月度提交趋势（柱状图）、活跃天数（面积图）、项目排行（横向柱状图）、语言分布（环形图）
- 💻 **CLI 新增命令** — `devdiary report` 年度报告、`devdiary watch` 监听服务管理
- 🎖️ **成就系统** — 自动解锁编码成就（千次提交、夜猫子、全栈工程师、周末战士等）

### V0.3 — 日记管理增强

### V0.2 — 统计数据真实化
- ✨ 新增 3 个统计聚合 API（提交趋势、编码热力图、智能洞察）
- 📊 统计概览页面全部图表改为真实 Git 数据驱动
- ⏱️ 时间范围筛选（7天/30天/90天）实时生效
- 💡 数据洞察自动分析最活跃时段、项目、连续编码天数

### V0.1 — MVP
- 🎉 初始版本发布
- 🔍 Git 提交扫描与分析
- 🤖 AI 日记生成（OpenAI / DeepSeek / 智谱 / 工蜂）
- 💻 CLI 工具（init / today / week / month / generate）
- 🌐 Web Dashboard 5 个页面
- 📅 自定义日期范围生成
- 📱 响应式布局，移动端适配

## 📄 许可证

MIT License

---

<a id="english"></a>

## 🌟 Introduction

DevDiary is an intelligent diary tool for developers that automatically generates dev diaries, weekly reports, and monthly reports by analyzing Git commit history with AI assistance. It helps you record, understand, and reflect on your coding life.

## ✨ Key Features

- 🔍 **Smart Git Scanning** — Automatically analyze commit history and understand code changes
- 🤖 **AI Content Generation** — Multiple AI backends (OpenAI / DeepSeek / Zhipu GLM / Gongfeng AI) with extensible provider abstraction
- 📄 **Multiple Styles** — Diary, tech blog, and report styles
- 📅 **Custom Date Range** — Generate diaries for any time period
- 💻 **CLI Tool** — One-command generation, fits into your workflow
- 🌐 **Web Dashboard** — Beautiful responsive web UI to visualize your coding journey
- 📊 **Real Data Analytics** — Commit trends, coding heatmap, language distribution — all driven by real Git data
- 💡 **Smart Insights** — Automatic analysis of peak coding hours, most active projects, coding streaks, and more
- 🏆 **Annual Developer Report** — GitHub Wrapped-style yearly coding recap with achievements
- 🔍 **Git Real-time Watcher** — Background service that monitors repos and auto-generates diaries on schedule

## 🚀 Quick Start

```bash
# Install
pip install -e .

# Install frontend dependencies
cd frontend && npm install && cd ..

# Initialize (configure AI provider & repos)
devdiary init

# Generate today's diary
devdiary today

# Generate weekly report
devdiary week

# Generate monthly report
devdiary month

# Custom date range
devdiary generate --from 2026-03-01 --to 2026-03-07

# Annual developer report
devdiary report

# Git watcher
devdiary watch             # Show status
devdiary watch --start     # Start background watcher
devdiary watch --stop      # Stop watcher

# Launch backend API
uvicorn src.devdiary.api.app:app --reload --port 8000

# Launch frontend dev server (another terminal)
cd frontend && npm run dev
```

Visit http://localhost:3000 for the Dashboard.

## 🛠️ Tech Stack

| Module | Technology |
|--------|-----------|
| Backend | Python 3.11+ / FastAPI / SQLAlchemy 2.0 (async) / Pydantic V2 |
| Frontend | Vue 3 / TypeScript / Vite / Naive UI / TailwindCSS / Pinia / ECharts |
| CLI | Click / Rich |
| AI | OpenAI / DeepSeek / Zhipu GLM / Gongfeng AI (extensible Provider pattern) |
| Database | SQLite (local) / PostgreSQL (team edition) |
| Migration | Alembic |

## 📄 License

MIT License
