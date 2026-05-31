# 业务概览 — 2026 世界杯仪表盘

## 产品概述

面向全球球迷的 2026 FIFA 世界杯实时仪表盘。功能包括赛程安排、实时比分、淘汰赛对阵图可视化、AI 驱动的比赛分析聊天机器人。

**视觉风格**：赛博朋克暗色毛玻璃（午夜深蓝 + 电子绿/青/品红强调色）。

## 当前状态

| 方面 | 状态 |
|------|------|
| 前端 UI | 完整视觉框架（所有组件已构建） |
| 数据来源 | 已接入后端 API |
| 后端 API | 完整实现（异常层级 + 中间件 + ORM 模型（5 张表）+ Pydantic Schema（8 个模块）+ Alembic 迁移 + 应用工厂（main.py）+ DI（dependencies.py）+ run.py 入口） |
| 状态管理 | Zustand 全局存储（4 个 store） |
| 路由 | 多页面（/、/groups、/groups/:group、/bracket、/stats、/teams/:code） |
| AI 服务 | 真实 SSE 流式（Deepseek API，打字机效果） |
| 实时更新 | WebSocket 已实现（实时比分、助威更新） |

## 核心业务实体

### 比赛（Match）
- 由 `id`（数字）标识
- 拥有两个 `Team` 对象、阶段、状态、比分、时间、场馆
- 状态流转：`upcoming` → `live` → `finished`
- 特殊标记：`isBigMatch`、`activityLevel`（0–100）

### 球队（Team）
- 由 3 字母代码标识（`BRA`、`FRA` 等）
- 属性：名称、代码、旗帜（emoji）、FIFA 排名

### 对阵图比赛（Bracket Match）
- 由字符串 `id` 标识（`"qf1"`、`"sf1"`、`"f1"` 等）
- 轮次类型：`R32`、`R16`、`QF`、`SF`、`3rd`、`F`
- 通过 `nextMatchId` 链接到下一场比赛

### 球队分析（AI）
- 5 维雷达图：进攻、防守、控球、定位球、状态（各 0–100）
- 胜/平概率、关键洞察列表

## 数据流（已实现）

```
page.tsx (状态拥有者)
├── timezone ──────→ Header (切换显示)
├── viewMode ──────→ Header (切换) → 切换 Timeline/Bracket
├── selectedDate ──→ DateTimeline (高亮) → MatchCardsGrid (按日期筛选)
│
├── [时间线模式]
│   ├── DateTimeline ──── API 获取比赛日期
│   └── MatchCardsGrid ── API 获取比赛数据 + WebSocket 实时更新
│
├── [对阵图模式]
│   └── TournamentBracket ── API 获取完整对阵树 (R32→F)
│
├── GroupStandings ──── API 获取 12 组积分榜
│
└── AICopilotPanel ──── SSE 流式聊天 → Deepseek API
```

## 数据流（目标 — 完整实现后）

```
page.tsx (状态拥有者)
├── [状态存储：Zustand]
│   ├── 用户偏好（timezone、viewMode、theme）
│   ├── 比赛数据缓存（来自 API）
│   ├── 实时更新（来自 WebSocket）
│   └── AI 聊天历史
│
├── [API 层]
│   ├── GET /api/matches?date=... → 比赛列表
│   ├── GET /api/bracket → 完整淘汰赛树
│   ├── GET /api/groups/:group → 积分榜
│   ├── POST /api/ai/chat → 流式 AI 响应
│   ├── GET /api/cheers/:matchId → 球迷投票数据
│   └── WS /ws/live → 实时比分更新
│
└── [路由]
    ├── / → 仪表盘（时间线/对阵图）
    ├── /groups → 小组积分榜
    ├── /groups/:group → 单组详情
    ├── /matches/:id → 比赛详情（弹窗）
    ├── /teams/:code → 球队详情
    ├── /bracket → 全屏对阵图
    └── /stats → 数据中心
```

## 赛事结构（2026 世界杯）

| 阶段 | 详情 |
|------|------|
| 小组赛 | 12 组（A–L），每组 4 支球队 |
| 小组赛比赛 | 72 场（每组 6 场） |
| 出线规则 | 每组前 2 名 + 8 支最佳第 3 名 = 32 支球队 |
| 淘汰赛 R32 | 16 场 |
| 淘汰赛 R16 | 8 场 |
| 四分之一决赛 | 4 场 |
| 半决赛 | 2 场 |
| 季军赛 | 1 场 |
| 决赛 | 1 场 |
| **总计** | **104 场** |

## 后端架构（已实现）

### 异常层级
```
AppException (基类, code=500)
├── NotFoundError (code=404)
├── ValidationError (code=422)
├── BusinessError (code=400)
└── ExternalServiceError (code=502)
```

### 中间件栈
- **ErrorHandlerMiddleware**：捕获所有异常 → 统一 `{code, data, message}` JSON 响应
- **CORS 中间件**：来源来自 `settings.CORS_ORIGINS`（环境变量可配置）
- **LoggingMiddleware**：记录 `method path → status (duration_ms)` 用于每个请求

### 统一 API 响应格式
所有 API 响应（成功和错误）遵循：`{"code": int, "data": T | null, "message": str}`

### ORM 模型（SQLAlchemy 2.0 Declarative）
```
Base (DeclarativeBase)
└── TimestampMixin (created_at, updated_at)
    ├── Team (id, name UNIQUE, name_zh, code UNIQUE, flag, fifa_ranking, group_label, confederation, world_cup_appearances)
    ├── Venue (id, name, name_zh, city, city_zh, country, country_zh, timezone, utc_offset, capacity)
    ├── Match (id, external_id UNIQUE, home/away_team_id FK→Team, venue_id FK→Venue, stage, group_label, round, match_day, kickoff_utc, status, home/away_score, is_big_match, activity_level, next_match_id FK→Match(self), position)
    ├── GroupStanding (id, team_id FK UNIQUE→Team, group_label, played, won, drawn, lost, goals_for, goals_against, goal_difference, points, position)
    └── MatchEvent (id, match_id FK→Match, event_type, minute, team_side, player_name)

关系：
  Team 1:N Match (home_matches, away_matches)
  Team 1:1 GroupStanding (standing)
  Venue 1:N Match (matches)
  Match 1:N MatchEvent (events, cascade delete)
  Match 自引用 next_match (对阵链接)
```

### Pydantic Schema（请求/响应验证）
```
common.py
├── ApiResponse[T]           # {code: int, data: T | null, message: str}
└── PaginatedResponse[T]     # {items: List[T], total, page, page_size}

team_schema.py
├── TeamCreate (DTO)         # name, name_zh, code, flag, fifa_ranking, group_label, confederation, world_cup_appearances
├── TeamUpdate (DTO)         # 所有字段可选
├── TeamResponse (VO)        # 完整球队数据
└── TeamListResponse (VO)    # 列表/下拉用的精简球队数据

match_schema.py
├── MatchQueryParams (DTO)   # date, stage, group, team, status 过滤器
├── MatchEventResponse (VO)  # event_type, minute, team_side, player_name
├── MatchResponse (VO)       # 嵌套 TeamListResponse + VenueResponse
└── MatchDetailResponse (VO) # 扩展 MatchResponse + 事件列表

venue_schema.py
└── VenueResponse (VO)       # name, name_zh, city, city_zh, country, country_zh, timezone, utc_offset, capacity

group_schema.py
├── GroupStandingResponse (VO) # team + 统计 (played/won/drawn/lost/GF/GA/GD/pts/pos)
└── GroupDetailResponse (VO)   # group_label + standings + matches

bracket_schema.py
├── BracketTeamResponse (VO)   # 球队槽位（支持 TBD 含 from_group/from_position）
├── BracketMatchResponse (VO)  # home/away BracketTeam + stage + status
├── BracketRoundResponse (VO)  # round_name + matches 列表
└── BracketTreeResponse (VO)   # rounds 列表（完整淘汰赛树）

cheer_schema.py
├── CheerVoteRequest (DTO)   # side: "home" | "away"
└── CheerResponse (VO)       # match_id, home count, away count

ai_schema.py
├── ChatRequest (DTO)        # messages + context + lang
├── SSEEvent (VO)            # type: thinking/answer/analysis/done/error + content/data
└── TeamAnalysisResponse (VO) # 雷达维度 + win_probability + insights

ws_schema.py
├── WSEventType (枚举)       # score_update, match_start, match_end, activity_update, cheer_update, bracket_update
└── WSMessage (VO)           # event + payload dict
```

所有响应模型使用 `from_attributes = True` 实现无缝 ORM → VO 转换。

### 数据库迁移（Alembic）
- **配置**：`alembic.ini` + `alembic/env.py`（通过 aiosqlite 异步模式）
- **数据库 URL**：从 `app.config.settings.DATABASE_URL` 动态解析
- **批处理模式**：`render_as_batch=True` 支持 SQLite ALTER TABLE
- **初始迁移**（`001_initial_schema.py`）：创建 teams、venues、group_standings、matches、match_events 含所有 FK 约束
- **场馆中文迁移**（`002_venue_zh_fields.py`）：为 venues 表添加 `name_zh`、`city_zh`、`country_zh` 列
- **命令**：`alembic upgrade head` / `alembic downgrade base`

## AI 预测技能

三个技能文件定义了比赛预测和冠亚军预测的推理框架：

- `skills/group_stage_predict.md` — 6 步推理（状态、H2H、战术、关键球员、主场优势、无形因素）
- `skills/knockout_stage_predict.md` — 5 步推理（状态、H2H、淘汰赛心理、战术对位、X 因素）
- `skills/冠亚军分析.md` — v2.0 自包含冠亚军预测（内嵌官方对阵表 + 7 大策略 + 5 步推理链 + 策略优先级矩阵 + 因子权重与规律迁移）

这些技能驱动后端 AI 服务（`POST /api/ai/chat`、`POST /api/ai/match-analysis`、`POST /api/ai/championship-analysis`）。

### 冠亚军预测分析

对阵图页面（`TournamentBracket`）提供「冠亚军预测」按钮，支持：
- 蒙特卡洛模拟 2000 次完整淘汰赛推演（遵循真实赛程时间线）
- 加载 v2.0 策略文件（含自包含的官方对阵表数据，不依赖外部数据注入）
- 7 大核心策略 + 策略优先级矩阵 + 数据降级方案（LLM 可直接执行）
- 输出 TOP 20 决赛场景及概率（含入选原因和数据约束）
- 可选策略文件选择器（shadcn Select 下拉）
- SSE 流式输出到 AI Copilot 面板

### AI 语言与格式控制

Prompt 构建层 (`prompt_builder.py`) 通过 `_SYSTEM_FRAGMENTS` 双语系统提示实现语言一致性和输出格式规范化：

- **语言强制**：`rules` 中包含显式语言指令（zh-CN: "思考过程和最终回答必须全部使用中文"；en-US: "reasoning and final answer must be in English"），确保 agent 思考和回答语种与项目选择一致。
- **Markdown 格式**：`build_skill_prompt()` 的用户指令明确要求以 Markdown 格式输出（二级标题分段、加粗/列表展示关键数据），保证分析结果格式稳定可渲染。
