# 实施计划：Python 后端架构搭建 (football-server)

## 概览

为 FIFA World Cup 2026 Dashboard 项目搭建完整的 Python 后端服务。当前 `football-server/` 目录为空，前端所有数据硬编码。后端将使用 **FastAPI + SQLite + Redis + Deepseek V4 Pro**，按照 CLAUDE.md 要求严格遵循三层架构（Controller -> Service -> Repository），提供 REST API、WebSocket 实时推送、SSE 流式 AI 聊天等能力。

## 技术选型

| 维度 | 选择 | 原因 |
|------|------|------|
| Web 框架 | FastAPI | 异步、类型安全、自动 OpenAPI 文档、原生 WebSocket/SSE 支持 |
| 结构化存储 | SQLite (aiosqlite) | 赛事数据相对固定，轻量部署，无额外运维成本 |
| 实时数据 | Redis | 高频数据（比分、活跃度、投票、WebSocket 状态），可关闭降级 |
| AI 服务 | Deepseek V4 Pro | 用户指定，OpenAI 兼容接口，支持流式输出 |
| 数据获取 | 网页爬虫 | 用户指定，从体育网站抓取实时数据 |
| ORM | SQLAlchemy 2.0 (async) | 成熟的异步 ORM，配合 Alembic 做迁移 |
| 数据校验 | Pydantic v2 | FastAPI 原生集成，DTO/VO 类型安全 |

## 目录结构

```
football-server/
├── pyproject.toml                  # 依赖管理 (uv/pip)
├── .env.example                    # 环境变量模板
├── .gitignore
├── alembic.ini                     # 数据库迁移配置
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 001_initial_schema.py
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI 应用工厂，lifespan 事件
│   ├── config.py                   # Pydantic Settings，环境变量配置
│   ├── dependencies.py             # FastAPI 依赖注入
│   ├── models/                     # SQLAlchemy ORM 模型
│   │   ├── base.py                 # DeclarativeBase, TimestampMixin
│   │   ├── team.py
│   │   ├── match.py
│   │   ├── venue.py
│   │   ├── group_standing.py
│   │   └── match_event.py
│   ├── schemas/                    # Pydantic 请求/响应模型 (DTO/VO)
│   │   ├── common.py               # ApiResponse[T], PaginatedResponse
│   │   ├── team_schema.py
│   │   ├── match_schema.py
│   │   ├── bracket_schema.py
│   │   ├── group_schema.py
│   │   ├── venue_schema.py
│   │   ├── cheer_schema.py
│   │   ├── ai_schema.py
│   │   └── ws_schema.py
│   ├── controllers/                # FastAPI 路由（薄层，仅参数解析）
│   │   ├── match_controller.py     # /api/matches
│   │   ├── bracket_controller.py   # /api/bracket
│   │   ├── team_controller.py      # /api/teams
│   │   ├── group_controller.py     # /api/groups
│   │   ├── venue_controller.py     # /api/venues
│   │   ├── cheer_controller.py     # /api/cheers
│   │   ├── ai_controller.py        # /api/ai/chat (SSE)
│   │   └── ws_controller.py        # /ws/live (WebSocket)
│   ├── services/                   # 业务逻辑层
│   │   ├── match_service.py
│   │   ├── bracket_service.py
│   │   ├── team_service.py
│   │   ├── group_service.py
│   │   ├── venue_service.py
│   │   ├── cheer_service.py
│   │   ├── ai_service.py           # Deepseek API 客户端，SSE 流式
│   │   ├── prompt_builder.py       # Skill 提示词构建
│   │   ├── live_service.py         # Redis 实时状态管理
│   │   └── websocket_manager.py    # WebSocket 连接管理
│   ├── repositories/               # 数据访问层
│   │   ├── base.py                 # 泛型 CRUD 基类
│   │   ├── team_repo.py
│   │   ├── match_repo.py
│   │   ├── venue_repo.py
│   │   ├── group_repo.py
│   │   └── match_event_repo.py
│   ├── redis/                      # Redis 客户端和键管理
│   │   ├── client.py               # 连接池
│   │   └── keys.py                 # 键模式定义
│   ├── scraping/                   # 外部数据爬虫模块
│   │   ├── base_scraper.py         # 限流、重试、错误处理
│   │   ├── fifa_scraper.py         # FIFA 官方数据
│   │   ├── live_score_scraper.py   # 实时比分源
│   │   └── data_sync.py            # 爬取数据 -> DB/Redis 同步
│   ├── exceptions/
│   │   └── exceptions.py           # AppException, NotFoundError 等
│   ├── middleware/
│   │   ├── error_handler.py        # 全局异常 -> 统一响应
│   │   ├── cors.py                 # CORS 配置
│   │   └── logging.py              # 请求日志
│   └── utils/
│       ├── timezone.py             # 时区转换工具
│       └── markdown_parser.py      # 解析 data/*.md 文件
├── scripts/                        # 数据初始化脚本
│   ├── seed_data.py                # 一键初始化入口
│   ├── seed_teams.py               # 48 支队伍
│   ├── seed_venues.py              # 16 座场馆
│   ├── seed_matches.py             # 72 小组赛 + 32 淘汰赛
│   └── generate_bracket.py         # 淘汰赛对阵关系
└── tests/
    ├── conftest.py                 # 测试 fixtures
    ├── test_match_controller.py
    ├── test_bracket_service.py
    ├── test_group_service.py
    └── test_ai_service.py
```

## 数据库设计

### SQLite 表结构

**teams** — 48 支参赛队伍

| 列名 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| name | VARCHAR(100) UNIQUE | 英文名 (Brazil) |
| name_zh | VARCHAR(100) | 中文名 (巴西) |
| code | VARCHAR(3) UNIQUE | 三字码 (BRA) |
| flag | VARCHAR(10) | Emoji 国旗 |
| fifa_ranking | INTEGER | FIFA 排名 |
| group_label | VARCHAR(1) | 分组 A-L |
| confederation | VARCHAR(3) | 足联 (UEFA/CONMEBOL 等) |
| world_cup_appearances | INTEGER | 历史世界杯参赛次数 |

**venues** — 16 座主办城市场馆

| 列名 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| name | VARCHAR(200) | 场馆名 |
| city | VARCHAR(100) | 城市 |
| country | VARCHAR(50) | 国家 |
| timezone | VARCHAR(50) | IANA 时区 |
| utc_offset | VARCHAR(6) | UTC 偏移 |
| capacity | INTEGER | 容量 |

**matches** — 104 场比赛

| 列名 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 1-104 |
| external_id | VARCHAR(20) UNIQUE | A_M1 / R32_01 |
| home/away_team_id | INTEGER FK | -> teams.id |
| venue_id | INTEGER FK | -> venues.id |
| stage | VARCHAR(20) | group/r32/r16/qf/sf/3rd/final |
| group_label | VARCHAR(1) | 仅小组赛 |
| round | INTEGER | 小组赛轮次 1-3 |
| match_day | DATE | 比赛日期 |
| kickoff_utc | DATETIME | UTC 开球时间 |
| status | VARCHAR(15) | upcoming/live/finished |
| home/away_score | INTEGER | 90 分钟比分 |
| is_big_match | BOOLEAN | 焦点比赛标记 |
| activity_level | INTEGER 0-100 | 比赛活跃度 |
| next_match_id | INTEGER FK | 胜者晋级到的比赛 |
| position | INTEGER | 轮次内位置序号 |

**group_standings** — 48 条积分记录

| 列名 | 类型 | 说明 |
|------|------|------|
| team_id | INTEGER FK UNIQUE | -> teams.id |
| group_label | VARCHAR(1) | A-L |
| played/won/drawn/lost | INTEGER | 比赛场次 |
| goals_for/goals_against | INTEGER | 进球 |
| goal_difference | INTEGER | 净胜球 |
| points | INTEGER | 积分 |
| position | INTEGER | 小组排名 |

**match_events** — 比赛事件

| 列名 | 类型 | 说明 |
|------|------|------|
| match_id | INTEGER FK | -> matches.id |
| event_type | VARCHAR(20) | goal/yellow_card/red_card 等 |
| minute | INTEGER | 比赛分钟 |
| team_side | VARCHAR(4) | home/away |
| player_name | VARCHAR(200) | 球员名 |

### Redis 键模式

| 模式 | 类型 | 用途 |
|------|------|------|
| `live:match:{id}` | HASH | 实时比分/状态/活跃度 |
| `cheers:match:{id}` | HASH | 球迷助威 {home: n, away: n} |
| `ws:connections` | SET | 活跃 WebSocket 连接 |
| `cache:groups` | STRING(JSON) | 小组积分缓存 |
| `cache:bracket` | STRING(JSON) | 对阵图缓存 |
| `scraper:lock` | STRING | 爬虫分布式锁 |

## 实施步骤

### 第一阶段：核心基础（项目搭建 + 数据库 + REST API）

**目标**：可运行的服务器，返回种子数据的完整 JSON 响应。

| 步骤 | 文件 | 动作 | 依赖 |
|------|------|------|------|
| 1.1 | `pyproject.toml` | 创建项目元数据和依赖声明 | 无 |
| 1.2 | `.env.example`, `.gitignore` | 创建配置模板 | 无 |
| 1.3 | `app/config.py` | Pydantic Settings 配置类 | 1.1 |
| 1.4 | `app/exceptions/exceptions.py` | 自定义异常层级 | 无 |
| 1.5 | `app/models/base.py` | DeclarativeBase + TimestampMixin | 1.1 |
| 1.6 | `app/models/team.py`, `venue.py`, `match.py`, `group_standing.py`, `match_event.py` | 5 个 ORM 模型 | 1.5 |
| 1.7 | `app/schemas/common.py` | ApiResponse[T] 统一响应 | 无 |
| 1.8 | `app/schemas/team_schema.py`, `match_schema.py`, `venue_schema.py`, `group_schema.py`, `bracket_schema.py` | 5 组 DTO/VO | 1.7 |
| 1.9 | `app/repositories/base.py` | 泛型异步 CRUD 基类 | 1.6 |
| 1.10 | `app/repositories/team_repo.py`, `match_repo.py`, `venue_repo.py`, `group_repo.py` | 4 个具体 Repository | 1.9 |
| 1.11 | `app/services/team_service.py`, `match_service.py`, `venue_service.py`, `group_service.py`, `bracket_service.py` | 5 个 Service | 1.10 |
| 1.12 | `app/controllers/` 下 5 个路由文件 | 5 组 Controller | 1.11 |
| 1.13 | `app/middleware/error_handler.py`, `cors.py` | 全局异常处理 + CORS | 1.4 |
| 1.14 | `app/dependencies.py` | 依赖注入提供者 | 1.6+1.11 |
| 1.15 | `app/main.py` | FastAPI 应用工厂 | 1.12+1.14 |
| 1.16 | `app/utils/markdown_parser.py` | Markdown 表格解析器 | 无 |
| 1.17 | `scripts/seed_*.py` + `generate_bracket.py` | 数据初始化脚本 | 1.16 |
| 1.18 | `alembic.ini` + `alembic/` | 数据库迁移配置 | 1.6 |

**验证**：
- `python scripts/seed_data.py` 成功插入 48 队伍 + 16 场馆 + 104 比赛 + 48 积分
- `uvicorn app.main:app --reload` 启动成功
- `GET /api/matches?date=2026-06-11` 返回正确 JSON
- `GET /api/groups/A` 返回积分榜 + 赛程
- `GET /api/bracket` 返回完整淘汰赛结构
- `/docs` 可访问 OpenAPI 文档

### 第二阶段：实时功能（Redis + WebSocket + 投票）

**目标**：实时比分推送、比赛活跃度、球迷助威投票。

| 步骤 | 文件 | 动作 |
|------|------|------|
| 2.1 | `app/redis/client.py`, `keys.py` | Redis 连接池和键定义 |
| 2.2 | `app/schemas/cheer_schema.py`, `ws_schema.py` | 投票和 WebSocket DTO |
| 2.3 | `app/services/cheer_service.py` | Redis 投票计数器 |
| 2.4 | `app/controllers/cheer_controller.py` | GET/POST /api/cheers/{matchId} |
| 2.5 | `app/services/live_service.py` | Redis 实时比赛状态 |
| 2.6 | `app/services/websocket_manager.py` | 连接注册 + 广播 |
| 2.7 | `app/controllers/ws_controller.py` | /ws/live 端点 |
| 2.8 | 修改 `match_service.py` | 同步 DB + Redis 状态 |
| 2.9 | 修改 `dependencies.py` | 增加 Redis 依赖 |

**验证**：
- WebSocket 客户端连接后收到 score_update 事件
- POST 投票后 GET 返回更新计数
- Redis 关闭时非实时接口正常工作

### 第三阶段：AI 集成（Deepseek + SSE 流式 + 预测）

**目标**：AI 聊天流式响应，比赛分析雷达图数据，小组赛/淘汰赛预测。

| 步骤 | 文件 | 动作 |
|------|------|------|
| 3.1 | `app/schemas/ai_schema.py` | 聊天请求/响应/分析 DTO |
| 3.2 | `app/services/prompt_builder.py` | Skill 提示词构建（6 步 + 5 步推理链） |
| 3.3 | `app/services/ai_service.py` | Deepseek API 客户端 + SSE 流 |
| 3.4 | `app/controllers/ai_controller.py` | POST /api/ai/chat SSE 端点 |

**验证**：
- curl POST /api/ai/chat 收到 SSE 流
- 询问特定对阵返回 TeamAnalysis 结构化数据
- 预测结果遵循 skills/ 中的推理链

### 第四阶段：数据爬虫管道

**目标**：定时后台爬取外部数据，同步到 DB/Redis。

| 步骤 | 文件 | 动作 |
|------|------|------|
| 4.1 | `app/scraping/base_scraper.py` | 限流/重试基类 |
| 4.2 | `app/scraping/fifa_scraper.py` | FIFA 官方数据爬虫 |
| 4.3 | `app/scraping/live_score_scraper.py` | 实时比分爬虫 |
| 4.4 | `app/scraping/data_sync.py` | 数据同步服务 |
| 4.5 | 修改 `app/main.py` | 添加后台任务启动 |

**验证**：启用爬虫后比分更新通过 WebSocket 推送到前端。

## 同步更新：Claude 配置和自动化工具链

完成架构搭建后，需同步更新以下文件：

| 文件 | 更新内容 |
|------|---------|
| `.claude/settings.local.json` | hooks 中 `check-refactor-threshold.sh` 增加 `*.py` 文件检查；docs sync hook 增加 `football-server/` 路径匹配 |
| `.claude/hooks/check-refactor-threshold.sh` | case 分支增加 `*.py` 文件类型的 600 行硬限制检查 |
| `.claude/skills/code-stats/SKILL.md` | 后端统计步骤改为 Python 文件统计 (`*.py`)，排除 `__pycache__`、`.venv`、`*.pyc` |
| `.claude/skills/sync-docs/SKILL.md` | 文档定位规则增加：若修改 `football-server/app/controllers` -> 更新 `agent-api-reference.md`；修改 `football-server/app/services` -> 更新 `business-overview.md` |
| `.docs/` 目录 | 创建 `agent-api-reference.md`、`agent-file-map.md`、`business-overview.md`（通过 /sync-docs 技能生成） |
| `CLAUDE.md` | 可选：在后端架构规范部分补充 Python 专项规则（类型提示、PEP 8、三层架构等） |

## 核心依赖

```
fastapi>=0.115
uvicorn[standard]>=0.34
sqlalchemy[asyncio]>=2.0
aiosqlite>=0.21
alembic>=1.14
redis[hiredis]>=5.0
pydantic>=2.0
pydantic-settings>=2.0
httpx>=0.28
python-dotenv>=1.0
```

## 风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| Markdown 解析中文字符边界情况 | 用实际 `2026_FIFA_World_Cup_Group_Stage.md` 做单元测试，建 48 队中英映射表 |
| 600 行限制被复杂 Service 超出 | 大 Service 控制在 400 行内，超出则抽取子模块 |
| Deepseek API 延迟/限流 | 30s 超时、SSE 流中返回错误消息、缓存常见预测 |
| Redis 不可用 | `REDIS_ENABLED=false` 降级为纯 DB 模式 |
| 爬虫被反爬 | 可配置多数据源，保留手动更新 API 作为后备 |
| 淘汰赛对阵关系复杂 | 种子阶段预建静态对阵树，仅填入队伍信息 |

## 成功标准

- [ ] Phase 1：所有 REST 端点返回匹配前端 TypeScript 接口的 JSON
- [ ] Phase 2：WebSocket 实时推送比分变化和投票更新
- [ ] Phase 3：AI 聊天 SSE 流式输出，预测遵循 skills/ 推理链
- [ ] Phase 4：爬虫数据同步到 API 响应
- [ ] 全局：所有文件 < 600 行，无调试代码，统一响应格式
