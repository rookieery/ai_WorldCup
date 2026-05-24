# FIFA World Cup 2026 Dashboard — 项目业务全景文档

> **文档定位**：本项目唯一的全局业务参考，整合前端需求与后端架构规划，作为开发、测试、产品验收的统一依据。
> **最后更新**：2026-05-24

---

## 一、项目概述

### 1.1 产品定义

2026 年 FIFA 世界杯（美国/加拿大/墨西哥联合举办）实时赛事仪表盘。面向全球球迷，提供赛程浏览、实时比分、淘汰赛对阵图、AI 赛事分析等核心功能。

### 1.2 视觉风格

赛博朋克暗色玻璃拟态（Glassmorphism）设计语言：

| 属性 | 值 |
|------|-----|
| 主色 | Electric Lime `#CCFF00` |
| 强调色 | Cyber Cyan `#00F0FF` |
| 次要强调 | Vivid Magenta `#FF00E5` |
| 高亮色 | Gold `#FFD700` |
| 背景色 | Midnight Navy `#020617` → `#0f172a` |
| 字体 | Geist（正文）+ Geist Mono（代码/数字） |
| 图标 | Lucide React |
| 图表 | Recharts |
| 卡片 | Glassmorphism（毛玻璃 + 半透明边框） |

### 1.3 国际化（i18n）

项目必须同时支持**中文（zh-CN）**和**英文（en-US）**两种语言：

| 维度 | 要求 |
|------|------|
| UI 文案 | 所有用户可见文本必须通过 i18n key 引用，严禁硬编码字符串 |
| 数据层 | 队伍名称、场馆信息等需同时提供中英文版本（后端 `name` / `name_zh` 字段） |
| 默认语言 | 根据浏览器 `Accept-Language` 自动检测，用户可手动切换 |
| 切换方式 | Header 区域增加语言切换控件（地球图标 + 下拉选择） |
| 路由策略 | 不使用 URL 前缀区分语言（`/zh/` / `/en/`），统一通过客户端状态管理 |
| AI 回复 | AI 聊天服务根据用户当前语言设置返回对应语言的回复 |
| 技术方案 | 前端推荐 `next-intl` 或自建轻量 i18n 上下文；后端通过 `Accept-Language` Header 或查询参数 `?lang=zh` 返回对应语言 |

---

## 二、赛事基础数据

| 维度 | 数值 |
|------|------|
| 参赛队伍 | 48 支（首次扩军至 48 队） |
| 小组数量 | 12 组（A-L），每组 4 队 |
| 小组赛 | 每组 6 场，共 72 场 |
| 晋级规则 | 每组前 2 名 + 8 支最佳第 3 名，共 32 队进入淘汰赛 |
| 淘汰赛 | R32(16场) → R16(8场) → QF(4场) → SF(2场) → 三四名(1场) → 决赛(1场)，共 32 场 |
| 总比赛场次 | 104 场 |
| 举办城市 | 16 座（美国 11 + 加拿大 2 + 墨西哥 3） |
| 比赛日期 | 2026 年 6 月 11 日 ~ 7 月 19 日 |

---

## 三、技术架构

### 3.1 全栈技术选型

| 层 | 技术 | 说明 |
|----|------|------|
| 前端框架 | Next.js 16 (App Router) + React 19 | SSR/CSR 混合，App Router 路由 |
| UI 库 | shadcn/ui + Tailwind CSS v4 | 语义化颜色变量，组件复用 |
| 前端状态 | Zustand（推荐） | 全局状态管理 |
| 后端框架 | FastAPI | 异步、类型安全、自动 OpenAPI 文档 |
| ORM | SQLAlchemy 2.0 (async) + Alembic | 异步 ORM，数据库迁移 |
| 结构化存储 | SQLite (aiosqlite) | 轻量部署，赛事数据相对固定 |
| 实时数据 | Redis (可选) | 比分、投票、WebSocket 状态 |
| AI 服务 | Deepseek V4 Pro | OpenAI 兼容接口，SSE 流式输出 |
| 数据获取 | 网页爬虫 | 从体育网站抓取实时数据 |
| 数据校验 | Pydantic v2 | DTO/VO 类型安全 |

### 3.2 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│  浏览器 / 移动端                                                 │
│  ┌──────────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  Next.js App      │  │  WebSocket   │  │  SSE (fetch)      │  │
│  │  (SSR + CSR)      │  │  Client      │  │  AI Chat Stream   │  │
│  └────────┬──────────┘  └──────┬───────┘  └────────┬──────────┘  │
└───────────┼─────────────────────┼──────────────────┼────────────┘
            │ REST API            │ WS               │ SSE
┌───────────┼─────────────────────┼──────────────────┼────────────┐
│  FastAPI 后端                                                    │
│  ┌────────▼──────────────────────▼──────────────────▼─────────┐  │
│  │  Controllers (路由层，参数校验)                              │  │
│  │  match / bracket / team / group / venue / cheer / ai / ws  │  │
│  └──────────────────────────┬─────────────────────────────────┘  │
│  ┌──────────────────────────▼─────────────────────────────────┐  │
│  │  Services (业务逻辑层)                                      │  │
│  │  业务编排 + AI Prompt 构建 + Redis 实时状态                  │  │
│  └──────────────────────────┬─────────────────────────────────┘  │
│  ┌──────────────────────────▼─────────────────────────────────┐  │
│  │  Repositories (数据访问层)                                  │  │
│  │  泛型 CRUD 基类 + 具体 Repo (team/match/venue/group/event) │  │
│  └──────────────────────────┬─────────────────────────────────┘  │
│                             │                                    │
│  ┌──────────────────────────▼──┐  ┌──────────────────────────┐  │
│  │  SQLite (aiosqlite)         │  │  Redis (可选)            │  │
│  │  赛程/队伍/积分/场馆/事件    │  │  实时比分/投票/缓存      │  │
│  └─────────────────────────────┘  └──────────────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Scraping Pipeline (后台定时)                                │ │
│  │  FIFA 官方 + 实时比分源 → 同步到 DB/Redis                    │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
            │
            │ OpenAI-Compatible API
┌───────────▼──────────────────────────────────────────────────────┐
│  Deepseek V4 Pro (AI 服务)                                       │
│  - 流式推理输出 (reasoning + answer)                              │
│  - 基于 skills/ 推理链的赛事预测                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 3.3 后端目录结构

```
football-server/
├── pyproject.toml                  # 依赖管理
├── .env.example                    # 环境变量模板
├── alembic.ini                     # 数据库迁移配置
├── alembic/versions/               # 迁移脚本
├── app/
│   ├── main.py                     # FastAPI 应用工厂
│   ├── config.py                   # Pydantic Settings
│   ├── dependencies.py             # 依赖注入
│   ├── models/                     # SQLAlchemy ORM 模型
│   ├── schemas/                    # Pydantic DTO/VO
│   ├── controllers/                # 路由层
│   ├── services/                   # 业务逻辑层
│   ├── repositories/               # 数据访问层
│   ├── redis/                      # Redis 客户端和键管理
│   ├── scraping/                   # 数据爬虫模块
│   ├── exceptions/                 # 自定义异常
│   ├── middleware/                 # 全局中间件
│   └── utils/                      # 工具函数
├── scripts/                        # 数据初始化
└── tests/                          # 测试
```

---

## 四、核心业务实体与数据模型

### 4.1 数据库表结构（SQLite）

#### teams — 48 支参赛队伍

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
| world_cup_appearances | INTEGER | 历史参赛次数 |

#### venues — 16 座主办城市场馆

| 列名 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| name | VARCHAR(200) | 场馆名 |
| city | VARCHAR(100) | 城市 |
| country | VARCHAR(50) | 国家 |
| timezone | VARCHAR(50) | IANA 时区 |
| utc_offset | VARCHAR(6) | UTC 偏移 |
| capacity | INTEGER | 容量 |

#### matches — 104 场比赛

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
| activity_level | INTEGER | 活跃度 0-100 |
| next_match_id | INTEGER FK | 胜者晋级到的比赛 |
| position | INTEGER | 轮次内位置序号 |

#### group_standings — 48 条积分记录

| 列名 | 类型 | 说明 |
|------|------|------|
| team_id | INTEGER FK UNIQUE | -> teams.id |
| group_label | VARCHAR(1) | A-L |
| played/won/drawn/lost | INTEGER | 场次 |
| goals_for/goals_against | INTEGER | 进球 |
| goal_difference | INTEGER | 净胜球 |
| points | INTEGER | 积分 |
| position | INTEGER | 小组排名 |

#### match_events — 比赛事件

| 列名 | 类型 | 说明 |
|------|------|------|
| match_id | INTEGER FK | -> matches.id |
| event_type | VARCHAR(20) | goal/yellow_card/red_card 等 |
| minute | INTEGER | 比赛分钟 |
| team_side | VARCHAR(4) | home/away |
| player_name | VARCHAR(200) | 球员名 |

### 4.2 Redis 键模式

| 模式 | 类型 | 用途 |
|------|------|------|
| `live:match:{id}` | HASH | 实时比分/状态/活跃度 |
| `cheers:match:{id}` | HASH | 球迷助威 {home: n, away: n} |
| `ws:connections` | SET | 活跃 WebSocket 连接 |
| `cache:groups` | STRING(JSON) | 小组积分缓存 |
| `cache:bracket` | STRING(JSON) | 对阵图缓存 |

### 4.3 前端 TypeScript 数据模型

```typescript
interface Team {
  name: string
  code: string
  flag: string
}

interface Match {
  id: number
  team1: Team
  team2: Team
  localTime: string
  hostTime: string
  venue: string
  hostCity: string
  stage: string
  status: "upcoming" | "live" | "finished"
  score1?: number
  score2?: number
  isBigMatch: boolean
  activityLevel: number
  fifaRanking1: number
  fifaRanking2: number
  round?: string
  matchEvents?: MatchEvent[]
}

interface MatchEvent {
  type: "goal" | "yellow_card" | "red_card" | "substitution" | "penalty" | "var"
  minute: number
  team: 1 | 2
  playerName: string
  detail?: string
}

interface BracketMatch {
  id: string
  round: "R32" | "R16" | "QF" | "SF" | "3rd" | "F"
  position: number
  team1: BracketTeam
  team2: BracketTeam
  status: "upcoming" | "live" | "completed"
  venue?: string
  matchTime?: string
  nextMatchId?: string
}

interface BracketTeam {
  name: string
  code: string
  flag: string
  score?: number
  isWinner?: boolean
  fromMatchId?: string
}

interface TeamAnalysis {
  team1: {
    name: string
    flag: string
    stats: { attack: number; defense: number; possession: number; setpieces: number; form: number }
    winProbability: number
  }
  team2: { /* 同 team1 */ }
  drawProbability: number
  keyInsights: string[]
}
```

---

## 五、API 契约

### 5.1 API 总览

```
/api
├── /matches
│   ├── GET /                    # 比赛列表 (date/stage/group/team/status 过滤)
│   ├── GET /live                # 当前进行中比赛
│   └── GET /:id                 # 单场比赛详情
├── /bracket
│   ├── GET /                    # 完整淘汰赛对阵图
│   └── GET /predictions         # AI 预测淘汰赛路径
├── /teams
│   ├── GET /                    # 所有队伍
│   ├── GET /:code               # 队伍详情
│   └── GET /:code/stats         # 队伍统计
├── /groups
│   ├── GET /                    # 所有小组积分
│   └── GET /:group              # 单组积分 + 赛程
├── /venues
│   └── GET /                    # 场馆列表 (含时区)
├── /cheers
│   ├── GET /:matchId            # 助威投票数据
│   └── POST /:matchId           # 提交投票
├── /ai
│   └── POST /chat               # AI 对话 (SSE 流式)
└── /ws
    └── /live                    # WebSocket 实时推送
```

### 5.2 统一响应格式

```json
{
  "code": 200,
  "data": { ... },
  "message": "success"
}
```

### 5.3 SSE 流式 AI 对话（参考实现）

基于 `D:\code\ai coding` 项目已验证的 SSE 实现，本项目后端采用以下模式：

#### 实现架构

```
前端 (fetch + ReadableStream)     后端 (FastAPI StreamingResponse)
     │                                      │
     │  POST /api/ai/chat                   │
     │  { messages, context, lang }          │
     │ ──────────────────────────────────>   │
     │                                      │  构建 Prompt (prompt_builder.py)
     │                                      │  调用 Deepseek API (stream=True)
     │  SSE: data: {"type":"thinking",..}   │  <── reasoning_content delta
     │  <────────────────────────────────── │
     │  SSE: data: {"type":"answer",...}    │  <── content delta
     │  <────────────────────────────────── │
     │  SSE: data: {"type":"analysis",...}  │  <── 结构化分析数据 (可选)
     │  <────────────────────────────────── │
     │  SSE: data: [DONE]                   │  流结束
     │  <────────────────────────────────── │
```

#### SSE 事件格式

```
data: {"type":"thinking","content":"让我分析一下这两支球队..."}\n\n
data: {"type":"answer","content":"巴西和法国的比赛将非常精彩..."}\n\n
data: {"type":"analysis","data":{"team1":{...},"team2":{...},"drawProbability":23,"keyInsights":[...]}}\n\n
data: [DONE]\n\n
```

#### 事件类型

| type | 说明 | 数据字段 |
|------|------|---------|
| `thinking` | AI 推理过程（Deepseek reasoning tokens） | `content: string` |
| `answer` | AI 正式回复内容 | `content: string` |
| `analysis` | 结构化比赛分析数据 | `data: TeamAnalysis` |
| `done` | 流结束 | 无 |

#### 前端消费方式

- **不使用**浏览器原生 `EventSource`（仅支持 GET）
- 使用 `fetch()` + `ReadableStream` 手动解析 SSE 行
- 支持双队列打字机效果（thinking 队列 + answer 队列）
- 支持 `AbortController` 中断流

#### 请求参数

```json
{
  "messages": [
    { "role": "user", "content": "分析巴西对阵法国" }
  ],
  "context": {
    "currentView": "bracket",
    "selectedDate": "2026-06-14",
    "timezone": "local"
  },
  "lang": "zh-CN"
}
```

### 5.4 WebSocket 实时推送事件

| 事件 | 触发条件 | 数据结构 |
|------|---------|---------|
| `score_update` | 比分变化 | `{matchId, team, score, event}` |
| `match_start` | 比赛开始 | `{matchId, status}` |
| `match_end` | 比赛结束 | `{matchId, status, score}` |
| `activity_update` | 活跃度变化 | `{matchId, activityLevel}` |
| `bracket_update` | 晋级更新 | `{matchId, winner, nextMatchId}` |

---

## 六、页面功能需求

### 6.1 页面布局

```
┌──────────────────────────────────────────────────────┐
│  Header (h-16, 固定顶部)                              │
│  [Trophy + Title]        [Lang] [TZ] [View Toggle]   │
├──────────────────────────────────┬───────────────────┤
│                                  │                   │
│  Main Content (~70%)             │  AI Copilot       │
│  Timeline 视图 / Bracket 视图     │  Sidebar (~30%)   │
│                                  │                   │
├──────────────────────────────────┴───────────────────┤
│  Footer Status Bar (h-10, 固定底部)                   │
└──────────────────────────────────────────────────────┘
```

### 6.2 Header 顶栏

| 需求编号 | 功能 | 说明 |
|----------|------|------|
| H-01 | 语言切换 | 中文/英文切换，影响全站 UI 文案和 AI 回复语言 |
| H-02 | 时区切换 | Local / Host City，联动全站比赛时间 |
| H-03 | 视图切换 | Timeline / Bracket 模式切换 |

### 6.3 Timeline 视图

| 需求编号 | 功能 | 说明 |
|----------|------|------|
| DT-01 | 日期-比赛联动 | 点击日期过滤该日比赛 |
| DT-02 | 赛事阶段标识 | 日期标注所属阶段（Group/R32/QF/SF/Final） |
| DT-03 | 今日自动定位 | 自动选中今日或最近有比赛的日期 |
| DT-04 | 有比赛标识 | 仅在有比赛的日期显示指示器 |
| DT-05 | 休息日处理 | 休息日灰显，显示空状态提示 |
| MC-01 | 比赛数据获取 | API 获取指定日期全部比赛 |
| MC-02 | 实时比分更新 | WebSocket 推送比分变化 |
| MC-03 | 比赛状态流转 | upcoming → live → finished 自动流转 |
| MC-04 | 时区联动 | 切换时区更新所有卡片时间显示 |
| MC-05 | Big Match 标记 | 焦点比赛金色发光效果 |
| MC-06 | 比赛活跃度 | 实时活跃度指标更新 |
| MC-07 | 球迷助威投票 | 后端存储 + 实时同步投票数据 |

### 6.4 Bracket 视图

| 需求编号 | 功能 | 说明 |
|----------|------|------|
| BK-01 | 完整淘汰赛 | R32→R16→QF→SF→3rd→F 全结构 |
| BK-02 | 对阵数据获取 | API 获取全部淘汰赛对阵 |
| BK-03 | 自动晋级更新 | 赛后胜者自动填充到下一轮 |
| BK-04 | 实时比分 | WebSocket 推送淘汰赛比分 |
| BK-05 | 获胜路径高亮 | 连接线高亮胜者晋级路径 |
| BK-06 | 三四名决赛 | 半决赛负者对决 |
| BK-07 | 横向滚动 | 完整结构支持横向滚动 |

### 6.5 AI Copilot 侧边栏

| 需求编号 | 功能 | 说明 |
|----------|------|------|
| AI-01 | AI 对话接口 | SSE 流式接入后端 AI 服务 |
| AI-02 | 上下文感知 | AI 感知当前赛事状态 |
| AI-03 | 赛事分析卡片 | 结构化分析渲染雷达图+概率条 |
| AI-04 | 快捷提问 | 预设问题按钮 |
| AI-05 | 多轮对话 | 支持上下文连续对话 |
| AI-06 | 打字机效果 | 流式逐字输出 |
| AI-07 | 预测免责 | 预测回复附带免责声明 |
| AI-08 | 移动端适配 | FAB 入口 + 抽屉展开 |

### 6.6 Footer 状态栏

| 需求编号 | 功能 | 说明 |
|----------|------|------|
| FT-01 | 实时状态指示 | 有 live 比赛时脉冲灯，否则显示倒计时 |
| FT-02 | 数据刷新时间 | 显示上次刷新实际时间戳 |
| FT-03 | 赛事统计 | 静态信息或进度统计 |

---

## 七、路由规划

| 路由 | 页面 | 说明 |
|------|------|------|
| `/` | 首页仪表盘 | Timeline / Bracket 视图切换 |
| `/groups` | 小组积分总览 | 12 组排名一览 |
| `/groups/:group` | 小组详情 | 积分榜 + 该组赛程 |
| `/matches/:id` | 比赛详情 | 阵容、事件、统计 |
| `/teams/:code` | 队伍详情 | 历史、球员、数据 |
| `/bracket` | 对阵图全屏 | 独立全屏对阵图 |
| `/stats` | 数据统计中心 | 射手榜、助攻榜等 |
| `/predict` | AI 预测中心 | 预测专题页 |

---

## 八、AI 预测技能

项目 `skills/` 目录下已定义 AI 推理框架：

### 8.1 小组赛预测（6 步推理）

`skills/group_stage_predict.md`：近期状态 → 历史交锋 → 战术体系 → 关键球员 → 主场优势 → 不可预测因素

### 8.2 淘汰赛预测（5 步推理）

`skills/knockout_stage_predict.md`：近期状态 → 历史交锋 → 淘汰赛心理 → 战术对决 → X 因素

### 8.3 支持的 AI 场景

| 场景 | 示例 | 预期返回 |
|------|------|---------|
| 赛程查询 | "明天有哪些比赛？" | 比赛列表 |
| 比赛预测 | "墨西哥胜率多少？" | TeamAnalysis + 自然语言分析 |
| 数据统计 | "目前射手榜" | 射手榜列表 |
| 淘汰赛预测 | "预测淘汰赛走势" | 完整淘汰赛路径 |
| 实时解读 | "巴西对法国现在什么情况？" | 实时解读 |
| 小组形势 | "韩国能从 A 组出线吗？" | 出线形势分析 |

---

## 九、前端待实现功能

| 编号 | 功能 | 优先级 | 说明 |
|------|------|--------|------|
| FE-01 | 小组积分榜 | P0 | 新增 Group Standings 组件 |
| FE-02 | 比赛详情弹窗 | P0 | 点击卡片查看详情 |
| FE-03 | 完整淘汰赛结构 | P0 | R32→R16→QF→SF→3rd→F |
| FE-04 | 射手榜 | P1 | 射手排行榜 |
| FE-05 | 队伍详情页 | P1 | 队伍详情路由页 |
| FE-06 | 比赛事件列表 | P1 | 实时事件流 |
| FE-07 | 通知/提醒 | P2 | 比赛开球提醒 |
| FE-08 | 分享功能 | P2 | 社交分享 |
| FE-09 | 多语言 (i18n) | P0 | 中文/英文切换 |
| FE-10 | 主题切换 | P2 | Dark/Light |

---

## 十、全局状态管理（Zustand）

| 状态域 | 说明 |
|--------|------|
| 用户偏好 | 语言、时区、视图模式、主题 |
| 实时数据 | 进行中比赛、比分、活跃度（WebSocket 更新） |
| 赛程缓存 | 已获取的赛程数据缓存 |
| AI 对话 | 聊天历史和流式状态 |
| 用户投票 | 各比赛助威投票状态 |

---

## 十一、实施阶段

### Phase 1 — MVP 核心（后端 API + 前端对接）

| 步骤 | 内容 |
|------|------|
| 1.1 | 后端项目搭建：FastAPI + SQLAlchemy + SQLite 基础框架 |
| 1.2 | ORM 模型 + 数据库迁移 + 种子数据脚本 |
| 1.3 | Repository 层（泛型 CRUD + 具体 Repo） |
| 1.4 | Service 层（match/team/group/bracket/venue） |
| 1.5 | Controller 层（REST API 路由） |
| 1.6 | 统一响应格式 + 全局异常处理 + CORS |
| 1.7 | 前端数据对接：替换硬编码为 API 调用 |
| 1.8 | 日期-比赛联动过滤 |
| 1.9 | 小组积分榜视图 |
| 1.10 | 完整淘汰赛对阵图（R32→Final） |
| 1.11 | i18n 基础架构搭建 + 中英文文案 |

**验收标准**：
- 种子数据成功写入（48 队 + 16 场馆 + 104 比赛 + 48 积分）
- `GET /api/matches?date=2026-06-11` 返回正确 JSON
- `GET /api/bracket` 返回完整淘汰赛结构
- 前端 Timeline 视图动态加载比赛数据
- 前端 Bracket 视图展示 R32→Final 全结构
- 中英文可切换，所有 UI 文案无硬编码

### Phase 2 — 实时功能

| 步骤 | 内容 |
|------|------|
| 2.1 | Redis 连接池 + 键管理 |
| 2.2 | 球迷助威投票（Redis 计数器 + API） |
| 2.3 | 实时比赛状态服务（Redis） |
| 2.4 | WebSocket 连接管理 + 广播 |
| 2.5 | 前端 WebSocket 集成 + 实时比分更新 |
| 2.6 | 比赛详情弹窗 |
| 2.7 | 前端全局状态管理（Zustand） |

**验收标准**：
- WebSocket 客户端连接后收到 score_update 事件
- POST 投票后 GET 返回更新计数
- Redis 关闭时非实时接口正常工作

### Phase 3 — AI 集成

| 步骤 | 内容 |
|------|------|
| 3.1 | Deepseek API 客户端 + SSE 流式输出 |
| 3.2 | Prompt Builder（基于 skills/ 推理链） |
| 3.3 | AI 对话 Controller（POST /api/ai/chat） |
| 3.4 | 前端 SSE 消费（fetch + ReadableStream） |
| 3.5 | 打字机效果 + 结构化分析卡片渲染 |

**验收标准**：
- curl POST /api/ai/chat 收到 SSE 流
- 分析对阵返回 TeamAnalysis 结构化数据
- 预测结果遵循 skills/ 推理链
- AI 回复语言与用户界面语言一致

### Phase 4 — 数据爬虫 + 完善

| 步骤 | 内容 |
|------|------|
| 4.1 | 爬虫基类（限流/重试） |
| 4.2 | FIFA 官方数据爬虫 |
| 4.3 | 实时比分爬虫 |
| 4.4 | 数据同步服务（爬取 → DB/Redis） |
| 4.5 | 射手榜 / 数据统计中心 |
| 4.6 | 队伍详情页 |
| 4.7 | 移动端 AI Copilot 适配 |

**验收标准**：
- 爬虫数据同步到 API 响应
- 比分更新通过 WebSocket 推送

---

## 十二、非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | 首屏 < 2s，WebSocket 延迟 < 500ms |
| 实时性 | 比分推送延迟 < 30s |
| 可用性 | 全球用户，CDN 部署 |
| 响应式 | 桌面 1920px+ / 平板 768px / 手机 375px |
| 浏览器 | Chrome / Firefox / Safari / Edge 最新两版 |
| 无障碍 | WCAG 2.1 AA |
| 文件限制 | 所有业务代码 < 600 行 |
| 代码规范 | 前端无 `any`，后端强制 Type Hints，严禁调试代码 |

---

## 十三、风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| Markdown 解析中文字符 | 用实际赛程文件做单元测试，建 48 队中英映射表 |
| 600 行限制 | Service 控制在 400 行内，超出抽离子模块 |
| Deepseek 延迟/限流 | 30s 超时、SSE 返回错误消息、缓存常见预测 |
| Redis 不可用 | `REDIS_ENABLED=false` 降级纯 DB 模式 |
| 爬虫反爬 | 多数据源，保留手动更新 API 后备 |
| 淘汰赛对阵复杂 | 种子阶段预建静态对阵树，仅填入队伍 |
| i18n 维护成本 | 提取所有文案到独立 JSON 文件，自动化缺失检测 |

---

## 十四、成功标准

- [ ] Phase 1：REST API 返回匹配前端接口的 JSON，中英文切换正常
- [ ] Phase 2：WebSocket 实时推送比分和投票更新
- [ ] Phase 3：AI 聊天 SSE 流式输出，预测遵循 skills/ 推理链
- [ ] Phase 4：爬虫数据同步到 API 响应
- [ ] 全局：所有文件 < 600 行，无调试代码，统一响应格式，i18n 完整
