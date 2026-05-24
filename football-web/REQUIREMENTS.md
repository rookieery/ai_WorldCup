# FIFA World Cup 2026 Dashboard — 完整功能需求规格说明书

> **项目名称**: football-web (World Cup 2026 Next-Gen Dashboard)
> **技术栈**: Next.js 16 (App Router) + React 19 + TypeScript + Tailwind CSS v4 + shadcn/ui
> **当前状态**: 纯前端 UI 视觉稿，所有数据硬编码，无后端 API、无路由、无全局状态管理
> **文档目的**: 基于现有 UI 提炼完整功能需求，为后端服务开发和前端交互完善提供依据

---

## 一、项目概述

2026 年 FIFA 世界杯（美国/加拿大/墨西哥联合举办）的实时赛事仪表盘。面向全球球迷，提供赛程浏览、实时比分、淘汰赛对阵图、AI 赛事分析等核心功能。整体采用赛博朋克暗色玻璃拟态（Glassmorphism）视觉风格。

### 1.1 赛事基础数据

| 维度 | 数值 |
|------|------|
| 参赛队伍 | 48 支（首次扩军至 48 队） |
| 小组数量 | 12 组（A-L），每组 4 队 |
| 小组赛 | 每组 6 场，共 72 场 |
| 晋级规则 | 每组前 2 名 + 8 支最佳第 3 名，共 32 队进入淘汰赛 |
| 淘汰赛 | 32强 → 16强 → 1/4决赛 → 半决赛 → 三四名决赛 → 决赛，共 32 场 |
| 总比赛场次 | 104 场 |
| 举办城市 | 16 座（美国 11 + 加拿大 2 + 墨西哥 3） |
| 比赛日期 | 2026 年 6 月 11 日 ~ 7 月 19 日 |

---

## 二、整体布局与导航

### 2.1 页面结构

```
┌──────────────────────────────────────────────────┐
│  Header (固定顶部, h-16)                          │
├────────────────────────────────────┬─────────────┤
│                                    │             │
│  Main Content (flex-1, ~70%)       │ AI Copilot  │
│  - Timeline 视图 / Bracket 视图    │ Sidebar     │
│                                    │ (~30%)      │
│                                    │             │
├────────────────────────────────────┴─────────────┤
│  Footer Status Bar (固定底部, h-10)               │
└──────────────────────────────────────────────────┘
```

### 2.2 Header 顶栏

**UI 元素**:
- 左侧：Trophy 图标 + "World Cup 2026" 标题 + "Next-Gen Dashboard" 副标题
- 右侧：两个切换控件
  - **时区切换**：Local（本地时间）/ Host City（主办城市时间），带 Globe 图标
  - **视图切换**：Timeline（时间线）/ Bracket（淘汰赛对阵图），带 LayoutGrid/GitBranch 图标

**功能需求**:

| 编号 | 需求 | 说明 |
|------|------|------|
| H-01 | 时区切换 | 切换后全站所有比赛时间同步切换为本地时间或主办城市当地时间。需后端返回每个主办城市的时区信息（UTC offset） |
| H-02 | 视图切换 | 在 Timeline（小组赛日期轴 + 比赛卡片列表）和 Bracket（淘汰赛对阵图）之间切换 |
| H-03 | 响应式 | Header 在移动端保持可用，控件可能需折叠或放入菜单 |

---

## 三、Timeline 视图（时间线模式）

### 3.1 日期时间轴 (DateTimeline)

**UI 元素**:
- 水平可滚动日期条，覆盖 6月11日 ~ 7月19日 共 40 天
- 每个日期节点显示：日期、星期、阶段标签（Group/R32/R16/QF/SF/3rd/Final/Rest）
- 左右箭头导航按钮
- 选中日期高亮（lime 绿发光），今日标记（cyan 青色）
- 阶段颜色编码：小组赛=lime, R32/R16=cyan, QF/SF=magenta, 3rd/Final=gold

**功能需求**:

| 编号 | 需求 | 说明 |
|------|------|------|
| DT-01 | 日期-比赛联动 | 点击某日期，下方比赛卡片列表过滤显示该日期所有比赛。当前 selectedDate prop 已传递但未实现过滤 |
| DT-02 | 赛事阶段标识 | 每个日期需根据实际赛程标注所属阶段。需后端提供赛程数据 |
| DT-03 | 今日自动定位 | 打开页面时自动选中今日，若今日无比赛则选中最近一个有比赛的日期 |
| DT-04 | 有比赛标识 | 仅在有比赛的日期下方显示圆点指示器，数据来源于赛程 API |
| DT-05 | 休息日处理 | 休息日（Rest）日期应灰显但可点击，点击后显示"今日无比赛"的空状态提示 |

### 3.2 比赛卡片网格 (MatchCardsGrid)

**UI 元素**:
- 标题栏："Matches" + 所选日期 + 颜色图例（Live/Big Match/Upcoming/Finished）
- 卡片网格：桌面端 2 列，移动端 1 列
- 每张比赛卡片包含：
  - 阶段标签（如 "Group A"、"Quarter Final"）
  - 状态指示（LIVE 脉冲动画 / BIG MATCH 火焰标签 / FT 全场结束）
  - 双方队伍信息：国旗 emoji + 三字码 + 全名
  - 比分显示：进行中=LED 发光效果，已结束=普通，未开始=vs
  - 双时区时间：本地时间 + 主办城市时间（含城市图标）
  - 场馆信息
  - 进行中比赛：比赛活跃度条（Activity Bar，带百分比动画）
  - 悬停展开：球迷助威计量器（Fan Cheer Meter），含投票按钮

**功能需求**:

| 编号 | 需求 | 说明 |
|------|------|------|
| MC-01 | 比赛数据获取 | 从后端 API 获取指定日期的全部比赛列表，包含队伍信息、比分、状态、时间、场馆等 |
| MC-02 | 实时比分更新 | 进行中的比赛（status=live）需实时推送比分变化，建议 WebSocket 或 SSE |
| MC-03 | 比赛状态流转 | 每场比赛的状态需按时间自动流转：upcoming → live → finished，前端自动刷新或接收推送 |
| MC-04 | 时区切换联动 | Header 中的时区切换需联动更新每张卡片上的本地时间/主办城市时间显示 |
| MC-05 | Big Match 标记 | 后端或前端根据关注度指标（球队名气、对决历史等）自动标记 Big Match，UI 上显示金色发光效果 |
| MC-06 | 比赛活跃度 | 进行中比赛的活跃度指标需实时更新，反映比赛节奏（射门、控球、危险进攻等综合评分） |
| MC-07 | 球迷助威投票 | 用户点击 Cheer 按钮后，需将投票数据发送到后端，并实时更新全局投票百分比。当前仅本地 state 增减 |
| MC-08 | 球迷助威数据初始化 | 每场比赛的初始投票比例需从后端获取（而非硬编码），反映所有用户的累计投票 |
| MC-09 | 日期过滤 | 根据 DateTimeline 选中的日期过滤比赛列表。当前 matches 数组固定为 4 场，需改为动态 |
| MC-10 | 空状态处理 | 当所选日期无比赛时，显示友好的空状态提示页面 |

**比赛数据模型**:

```typescript
interface Match {
  id: number
  team1: Team          // 主队
  team2: Team          // 客队
  localTime: string    // 本地开球时间
  hostTime: string     // 主办城市开球时间
  venue: string        // 场馆名称
  hostCity: string     // 主办城市
  stage: string        // 比赛阶段 (Group A / R32 / QF / SF / Final 等)
  status: "upcoming" | "live" | "finished"
  score1?: number      // 主队比分
  score2?: number      // 客队比分
  isBigMatch: boolean  // 是否为焦点比赛
  activityLevel: number // 比赛活跃度 0-100
  fifaRanking1: number // 主队 FIFA 排名
  fifaRanking2: number // 客队 FIFA 排名
  round?: string       // 轮次（小组赛第几轮）
  matchEvents?: MatchEvent[] // 比赛事件（进球、红黄牌等）
}

interface Team {
  name: string         // 队伍全名
  code: string         // 三字码 (BRA/FRA/等)
  flag: string         // 国旗 emoji 或图片 URL
}

interface MatchEvent {
  type: "goal" | "yellow_card" | "red_card" | "substitution" | "penalty" | "var"
  minute: number
  team: 1 | 2
  playerName: string
  detail?: string
}
```

---

## 四、Bracket 视图（淘汰赛对阵图）

### 4.1 TournamentBracket 对阵图

**UI 元素**:
- 标题："Knockout Stage — Road to Glory"
- 三列对阵结构：1/4决赛（4场） → 半决赛（2场） → 决赛（1场）
- 每场对阵卡片（BracketCard）：
  - 轮次标签（QUARTER-FINAL / SEMI-FINAL / FINAL）
  - 双方队伍行：国旗 + 三字码 + 比分（获胜方高亮）
  - LIVE 状态顶部渐变条 + 闪电图标
  - 场馆和时间信息
  - 决赛卡片带 Trophy 图标和金色发光
- SVG 连接线：带渐变色和发光效果，获胜路径动态高亮
- 底部图例：Live Match / Winner Advances / Advancement Path

**功能需求**:

| 编号 | 需求 | 说明 |
|------|------|------|
| BK-01 | 完整淘汰赛结构 | 当前仅展示 QF→SF→Final，需扩展为完整的 R32→R16→QF→SF→3rd/Final 结构 |
| BK-02 | 对阵数据获取 | 从后端 API 获取淘汰赛全部对阵数据，包括已确定的和待定（TBD）的 |
| BK-03 | 自动晋级更新 | 比赛结束后，获胜方自动填充到下一轮对阵的对应位置 |
| BK-04 | 实时比分更新 | 进行中的淘汰赛比赛需实时推送比分 |
| BK-05 | 获胜路径高亮 | 已完赛的比赛，连接线需高亮获胜方的晋级路径（带发光动画） |
| BK-06 | 三四名决赛 | 需增加半决赛负者之间的三四名决赛展示 |
| BK-07 | 对阵卡片交互 | 点击对阵卡片可查看比赛详情（阵容、进球事件、统计数据等） |
| BK-08 | 横向滚动 | 完整的 R32→Final 结构在桌面端需支持横向滚动，移动端需考虑纵向布局或缩放 |

**淘汰赛数据模型**:

```typescript
interface BracketMatch {
  id: string
  round: "R32" | "R16" | "QF" | "SF" | "3rd" | "F"
  position: number      // 在该轮次中的位置序号
  team1: BracketTeam
  team2: BracketTeam
  status: "upcoming" | "live" | "completed"
  venue?: string
  matchTime?: string    // 开球时间
  nextMatchId?: string  // 胜者晋级到的下一场 ID
}

interface BracketTeam {
  name: string
  code: string
  flag: string
  score?: number
  isWinner?: boolean
  fromMatchId?: string  // 从哪场比赛晋级而来
}
```

---

## 五、AI Copilot 侧边栏

### 5.1 AICopilotPanel 聊天面板

**UI 元素**:
- 面板标题："World Cup AI Copilot — Real-time analytics engine"
- 快捷提问按钮：4 个预设问题（Who plays tomorrow? / Mexico win probability? / Top scorers so far / Bracket predictions）
- 聊天消息区：
  - 用户消息（右对齐，lime 绿背景）
  - AI 回复（左对齐，暗色背景）
  - 分析类回复包含 AnalysisCard 组件
- AnalysisCard 包含：
  - 胜率概率条（Win Probability Bar）：双方胜率 + 平局概率
  - 双方雷达图（MiniRadarChart）：5 维能力对比（ATK/DEF/FORM/POSS/SET）
  - 关键洞察列表（Key Insights）
  - 统计维度图例
- 输入框 + 发送按钮（聚焦时发光效果）
- 思考中动画指示器（三个脉冲圆点）
- 底部免责声明："AI predictions are for entertainment purposes only"

**功能需求**:

| 编号 | 需求 | 说明 |
|------|------|------|
| AI-01 | AI 对话接口 | 接入后端 AI 服务，支持自然语言问答。用户发送消息后调用 AI API 获取回复，而非当前 2 秒延迟的硬编码模拟 |
| AI-02 | 上下文感知 | AI 需感知当前赛事状态（已完赛比赛结果、小组积分、进行中比赛等），以提供准确的分析和预测 |
| AI-03 | 赛事分析卡片 | 当用户询问特定对阵分析时，AI 返回结构化的分析数据（TeamAnalysis），前端渲染为雷达图+概率条+洞察列表 |
| AI-04 | 快捷提问 | 快捷按钮点击后将文本填入输入框（当前已实现），用户按回车或点击发送后触发 AI 请求 |
| AI-05 | 多轮对话 | 支持上下文连续对话，AI 能理解之前的提问内容 |
| AI-06 | 打字机效果 | AI 回复采用逐字/逐段流式输出效果（Streaming），而非一次性显示 |
| AI-07 | 预测免责 | 所有涉及预测的回复需附带免责声明 |
| AI-08 | 移动端适配 | 侧边栏在 lg 断点以下隐藏，需提供浮动入口按钮（FAB）点击后以抽屉/全屏方式展开 |
| AI-09 | 消息持久化 | 可选：聊天历史记录关联用户身份，刷新页面后保留 |

**AI 分析数据模型**:

```typescript
interface TeamAnalysis {
  team1: {
    name: string
    flag: string
    stats: {
      attack: number      // 攻击力 0-100
      defense: number     // 防守力 0-100
      possession: number  // 控球能力 0-100
      setpieces: number   // 定位球能力 0-100
      form: number        // 近期状态 0-100
    }
    winProbability: number // 胜率百分比
  }
  team2: { /* 同 team1 结构 */ }
  drawProbability: number  // 平局概率
  keyInsights: string[]    // 关键洞察，3-5 条
}
```

**支持的 AI 问答场景**:

| 场景 | 示例问题 | 预期返回 |
|------|---------|---------|
| 赛程查询 | "Who plays tomorrow?" | 明日比赛列表（队伍、时间、场馆） |
| 比赛预测 | "Mexico win probability?" | TeamAnalysis 结构化数据 + 自然语言分析 |
| 数据统计 | "Top scorers so far" | 射手榜列表（排名、球员、球队、进球数） |
| 淘汰赛预测 | "Bracket predictions" | AI 预测的完整淘汰赛路径 |
| 实时解读 | "What's happening in BRA vs FRA?" | 进行中比赛的实时解读（进球、关键事件、节奏分析） |
| 小组形势 | "Can Korea advance from Group A?" | 小组出线形势分析（需积分计算） |

---

## 六、Footer 状态栏

**UI 元素**:
- 左侧：绿色脉冲点 + "Live Updates Active" + "48 Teams • 16 Host Cities • 104 Matches"
- 右侧："Data refreshed: Just now" + "FIFA World Cup 2026™"

**功能需求**:

| 编号 | 需求 | 说明 |
|------|------|------|
| FT-01 | 实时状态指示 | 当有进行中比赛时脉冲点亮起并显示"Live Updates Active"；无进行中比赛时显示"Next match in XX:XX"倒计时 |
| FT-02 | 数据刷新时间 | 显示上次数据刷新的实际时间戳，而非固定的"Just now" |
| FT-03 | 赛事统计 | "48 Teams / 16 Host Cities / 104 Matches" 可作为静态信息，或根据赛事进度显示"XX of 104 Matches Completed" |

---

## 七、后端 API 需求

### 7.1 API 概览

基于前端功能需求，后端需提供以下 API 模块：

```
/api
├── /matches
│   ├── GET /                    # 获取比赛列表（支持日期、阶段、队伍过滤）
│   ├── GET /:id                 # 获取单场比赛详情
│   └── GET /live                # 获取当前进行中的比赛
├── /bracket
│   ├── GET /                    # 获取完整淘汰赛对阵图
│   └── GET /predictions         # AI 预测淘汰赛路径
├── /teams
│   ├── GET /                    # 获取所有队伍信息
│   ├── GET /:code               # 获取单支队伍详情
│   └── GET /:code/stats         # 获取队伍统计数据
├── /groups
│   ├── GET /                    # 获取所有小组积分榜
│   └── GET /:group              # 获取单个小组积分和赛程
├── /venues
│   └── GET /                    # 获取所有场馆信息（含时区）
├── /cheers
│   ├── GET /:matchId            # 获取某场比赛的球迷投票数据
│   └── POST /:matchId           # 提交球迷投票
├── /ai
│   └── POST /chat               # AI 对话接口（支持 streaming）
└── /ws
    └── /live                    # WebSocket 实时推送（比分更新、比赛状态变化）
```

### 7.2 核心 API 详细规格

#### GET /api/matches

获取比赛列表，支持多种过滤参数。

**请求参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| date | string | 按日期过滤，格式 "YYYY-MM-DD" 或 "Jun 14" |
| stage | string | 按阶段过滤: group / r32 / r16 / qf / sf / final |
| group | string | 按小组过滤: A-L |
| team | string | 按队伍三字码过滤 |
| status | string | 按状态过滤: upcoming / live / finished |
| timezone | string | 返回时间的目标时区 |

**响应体**:

```json
{
  "date": "2026-06-14",
  "matches": [
    {
      "id": 1,
      "stage": "Group A",
      "round": 2,
      "status": "live",
      "isBigMatch": false,
      "activityLevel": 85,
      "team1": { "name": "Mexico", "code": "MEX", "flag": "🇲🇽", "fifaRanking": 15 },
      "team2": { "name": "Canada", "code": "CAN", "flag": "🇨🇦", "fifaRanking": 27 },
      "score": { "team1": 2, "team2": 1 },
      "localTime": "2026-06-14T15:00:00-04:00",
      "hostTime": "2026-06-14T12:00:00-06:00",
      "venue": "Azteca Stadium",
      "hostCity": "Mexico City",
      "hostCityTimezone": "America/Mexico_City"
    }
  ]
}
```

#### GET /api/bracket

获取完整淘汰赛对阵图数据。

**响应体**:

```json
{
  "rounds": [
    {
      "name": "Round of 32",
      "shortName": "R32",
      "matches": [
        {
          "id": "r32_1",
          "position": 1,
          "status": "upcoming",
          "team1": { "name": "1st Group A", "code": "TBD", "flag": "🏳️", "fromGroup": "A", "fromPosition": 1 },
          "team2": { "name": "2nd Group B", "code": "TBD", "flag": "🏳️", "fromGroup": "B", "fromPosition": 2 },
          "nextMatchId": "r16_1",
          "venue": "MetLife Stadium",
          "matchTime": "2026-06-28T18:00:00-04:00"
        }
      ]
    },
    {
      "name": "Round of 16",
      "shortName": "R16",
      "matches": [/* ... */]
    },
    {
      "name": "Quarter-Finals",
      "shortName": "QF",
      "matches": [/* ... */]
    },
    {
      "name": "Semi-Finals",
      "shortName": "SF",
      "matches": [/* ... */]
    },
    {
      "name": "Third Place",
      "shortName": "3rd",
      "matches": [/* ... */]
    },
    {
      "name": "Final",
      "shortName": "F",
      "matches": [/* ... */]
    }
  ]
}
```

#### POST /api/ai/chat

AI 对话接口，支持 Server-Sent Events 流式返回。

**请求体**:

```json
{
  "messages": [
    { "role": "user", "content": "Analyze the Brazil vs France matchup" }
  ],
  "context": {
    "currentView": "bracket",
    "selectedDate": "Jun 14",
    "timezone": "local"
  }
}
```

**响应（流式 SSE）**:

```
data: {"type": "text", "content": "Here's my analysis"}
data: {"type": "analysis", "data": {"team1": {...}, "team2": {...}, "drawProbability": 23, "keyInsights": [...]}}
data: {"type": "done"}
```

#### GET /api/groups/:group

获取小组积分榜和赛程。

**响应体**:

```json
{
  "group": "A",
  "standings": [
    {
      "position": 1,
      "team": { "name": "Mexico", "code": "MEX", "flag": "🇲🇽" },
      "played": 2,
      "won": 2,
      "drawn": 0,
      "lost": 0,
      "goalsFor": 5,
      "goalsAgainst": 1,
      "goalDifference": 4,
      "points": 6,
      "advanceProbability": 98
    }
  ],
  "matches": [
    {
      "id": "A_M1",
      "round": 1,
      "home": { "name": "Mexico", "code": "MEX", "flag": "🇲🇽" },
      "away": { "name": "South Africa", "code": "RSA", "flag": "🇿🇦" },
      "score": "2-0",
      "date": "2026-06-11",
      "venue": "Azteca Stadium",
      "status": "finished"
    }
  ]
}
```

### 7.3 WebSocket 实时推送

**连接地址**: `ws://host/api/ws/live`

**推送事件类型**:

| 事件 | 触发条件 | 数据结构 |
|------|---------|---------|
| `score_update` | 比分变化 | `{ matchId, team, score, event: { type: "goal", player, minute } }` |
| `match_start` | 比赛开始 | `{ matchId, status: "live" }` |
| `match_end` | 比赛结束 | `{ matchId, status: "finished", score }` |
| `activity_update` | 比赛活跃度变化 | `{ matchId, activityLevel }` |
| `bracket_update` | 淘汰赛晋级更新 | `{ matchId, winner, nextMatchId }` |

---

## 八、前端交互需求（当前缺失功能）

### 8.1 需新增的功能模块

| 编号 | 功能 | 优先级 | 说明 |
|------|------|--------|------|
| FE-01 | 小组积分榜 | P0 | 当前 UI 完全缺失小组积分榜视图，需新增 Group Standings 组件，展示 12 个小组的排名表 |
| FE-02 | 比赛详情弹窗 | P0 | 点击比赛卡片或对阵卡片，弹出比赛详情（阵容、进球事件、技术统计、比赛时间线） |
| FE-03 | 完整淘汰赛结构 | P0 | 将当前 QF→SF→Final 扩展为 R32→R16→QF→SF→3rd→Final 完整对阵图 |
| FE-04 | 射手榜 | P1 | 展示赛事射手榜（排名、球员名、球队、进球数、助攻数） |
| FE-05 | 队伍详情页 | P1 | 点击队伍可查看详情（历史战绩、球员名单、小组赛成绩、赛事数据统计） |
| FE-06 | 比赛事件列表 | P1 | 进行中/已结束比赛的实时事件流（进球、黄/红牌、换人、VAR） |
| FE-07 | 通知/提醒 | P2 | 用户可设置比赛开球提醒（浏览器通知 / 姑息设置） |
| FE-08 | 分享功能 | P2 | 比赛结果/对阵图的社交分享 |
| FE-09 | 多语言 | P2 | 支持中文/英文切换 |
| FE-10 | 主题切换 | P2 | 已有 ThemeProvider 但未启用，支持 Dark/Light 主题切换 |

### 8.2 路由规划

当前仅有一个 `/` 路由，建议扩展为：

```
/                           → 首页仪表盘（Timeline/Bracket 视图）
/groups                     → 小组积分榜总览
/groups/:group              → 单个小组详情（积分榜 + 赛程）
/matches/:id                → 比赛详情页
/teams/:code                → 队伍详情页
/bracket                    → 淘汰赛对阵图（独立全屏页面）
/stats                      → 数据统计中心（射手榜、助攻榜等）
/predict                    → AI 预测中心
```

### 8.3 全局状态管理

当前无全局状态管理，建议引入状态管理方案（推荐 Zustand）管理以下状态：

| 状态 | 说明 |
|------|------|
| 用户偏好 | 时区选择、视图模式、主题等 |
| 实时数据 | 进行中比赛列表、比分、活跃度（从 WebSocket 更新） |
| 赛程缓存 | 已获取的赛程数据缓存，避免重复请求 |
| AI 对话历史 | 聊天消息持久化 |
| 用户投票 | 各比赛的球迷助威投票状态 |

---

## 九、数据源参考

### 9.1 已有数据文件

项目 `data/` 目录下已包含以下参考数据：

| 文件 | 内容 | 用途 |
|------|------|------|
| `2022_FIFA_World_Cup_Results.md` | 2022 卡塔尔世界杯全部 64 场比赛结果（中文） | 历史数据参考，可用于 AI 预测模型的训练数据 |
| `2026_FIFA_World_Cup_Group_Stage.md` | 2026 世界杯小组赛完整赛程（12 组共 72 场，结果待定） | 后端小组赛赛程的初始数据源 |

### 9.2 已有 AI 技能（Skills）

项目 `skills/` 目录下已定义两个 AI 预测技能：

| 技能 | 说明 | 与 Web 项目的关系 |
|------|------|------------------|
| `group_stage_predict.md` | 小组赛单场预测（6 步推理） | 后端 AI 服务的核心逻辑，需封装为 API |
| `knockout_stage_predict.md` | 淘汰赛单场预测（5 步推理） | 同上 |

**这些 skill 文件定义了 AI 的推理框架和输入输出规范，后端 AI 服务应基于此实现。**

---

## 十、非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | 首屏加载 < 2s，WebSocket 消息延迟 < 500ms |
| 实时性 | 比分更新推送延迟 < 30s（与官方数据源延迟一致） |
| 可用性 | 支持全球用户访问，考虑 CDN 部署 |
| 响应式 | 支持桌面端（1920px+）、平板（768px）、手机（375px） |
| 浏览器 | Chrome / Firefox / Safari / Edge 最新两个版本 |
| 无障碍 | 符合 WCAG 2.1 AA 标准（当前 a11y 待完善） |
| 国际化 | 首期支持英文，预留多语言架构 |
| 数据准确性 | 比分、赛程数据需与 FIFA 官方数据源同步 |

---

## 十一、实施优先级建议

### Phase 1 — MVP（最小可用产品）

1. **后端 API 基础搭建**：赛程数据 CRUD、小组积分榜 API
2. **前端数据对接**：替换硬编码数据为 API 调用
3. **日期-比赛联动**：实现 DateTimeline 点击过滤比赛
4. **小组积分榜**：新增小组积分榜视图
5. **完整淘汰赛对阵图**：扩展为 R32→Final 完整结构

### Phase 2 — 实时与交互

1. **WebSocket 实时推送**：比分、比赛状态实时更新
2. **比赛详情弹窗**：点击卡片查看完整比赛信息
3. **AI 对话接入**：替换模拟 AI 为真实后端服务
4. **球迷助威投票**：后端存储 + 实时同步

### Phase 3 — 完善与增值

1. **射手榜/数据统计中心**
2. **队伍详情页**
3. **移动端 AI Copilot 适配**
4. **多语言支持**
5. **比赛提醒/通知**

---

## 附录 A：UI 设计规范摘要

| 属性 | 值 |
|------|-----|
| 主题色 | Electric Lime `#CCFF00` |
| 强调色 | Cyber Cyan `#00F0FF` |
| 次要强调 | Vivid Magenta `#FF00E5` |
| 高亮色 | Gold `#FFD700` |
| 背景色 | Midnight Navy `#020617` → `#0f172a` |
| 卡片风格 | Glassmorphism（毛玻璃 + 半透明边框） |
| 字体 | Geist（正文）+ Geist Mono（代码/数字） |
| 图标库 | Lucide React |
| 图表库 | Recharts（已安装未使用） |
| 动画 | Tailwind + 自定义 CSS 动画（发光、脉冲、网格渐变等） |
