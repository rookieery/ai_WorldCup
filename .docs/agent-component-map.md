# Agent 组件注册表

> `football-web` 的 React 组件导航。

## 页面组件

### `app/page.tsx` — `WorldCupDashboard`
- **类型**：客户端组件（`"use client"`）
- **状态**：`timezone`、`viewMode`、`selectedDate`（均为 `useState`）、`agentPanelWidth`（AI 侧边栏宽度，`useRef` + `useCallback` 实现拖拽缩放）
- **布局**：Header → 主区域（时间线|对阵图）+ AI 侧边栏（可拖拽分割线缩放，min=340px，max=33.33vw）→ Footer
- **Props 流向**：状态直接传递给子组件
- **功能**：时间线视图中的小组赛快捷入口（Trophy 图标 → `/groups`）；移动端 AI 助手（`AICopilotMobile`）含 FAB + 底部抽屉 Sheet；桌面端 AI 侧边栏支持拖拽分割线调整宽度

### `app/bracket/page.tsx` — `BracketPage`
- **类型**：客户端组件（`"use client"`）
- **布局**：Header → TournamentBracket → Footer（全宽，无侧边栏）
- **封装**：`I18nProvider` 用于独立页面的 i18n 上下文
- **功能**：通过 `/bracket` 访问的全屏对阵图视图

### `app/teams/[code]/page.tsx` — `TeamDetailPage`
- **类型**：客户端组件（`"use client"`）
- **状态**：`timezone`、`viewMode`、`teamData`（TeamStatsData）、`loading`、`error`
- **布局**：Header → 返回链接 → TeamHeader + (GroupStandingCard | FinishedMatchesCard + UpcomingMatchesCard) → Footer
- **路由**：动态路由 `/teams/[code]`，code 为 3 字母球队代码（如 BRA、USA）
- **API**：`getTeamStats(code)` 来自 `@/lib/api/teams` — 获取球队资料、积分和比赛列表
- **子组件**：`TeamHeader`、`GroupStandingCard`、`StatItem`、`FinishedMatchesCard`、`UpcomingMatchesCard`、`MatchRow`、`UpcomingMatchRow`
- **i18n**：使用 `teamDetail.*` 命名空间键管理所有文本
- **行数**：~570

## 仪表盘组件（`components/dashboard/`）

### `header.tsx` — `Header`
- **Props**：`timezone`、`viewMode`、`onTimezoneChange`、`onViewModeChange`
- **i18n**：使用 `useTranslation()` Hook 管理所有文本；导入 `Locale` 类型用于语言切换
- **UI**：Trophy 图标 + 标题、语言切换（Globe + Select 下拉：zh-CN/en-US）、时区切换（Clock 图标 + Switch）、视图切换（时间线/对阵图）
- **语言切换**：从 i18n 上下文读取 `locale`/`setLocale`，渲染为毛玻璃卡片 + Globe 图标 + shadcn Select
- **依赖**：`Switch`、`Label`、`Select`/`SelectContent`/`SelectItem`/`SelectTrigger`/`SelectValue`（shadcn）、`lucide-react` 图标（Globe、Clock、LayoutGrid、GitBranch、Trophy）
- **行数**：~139

### `date-timeline.tsx` — `DateTimeline`
- **Props**：`selectedDate`、`onDateSelect`
- **数据**：通过 `getMatchDates({ timezone })` 从 API 获取 — 动态比赛日期含阶段标签；自动发送用户本地时区（`Intl.DateTimeFormat().resolvedOptions().timeZone`）
- **格式分离**：原始日期数据（`rawDates` 状态）与格式化标签（`useMemo` 从 `t` 派生）分离 — locale 切换时自动重新格式化
- **Locale 重新获取**：`useEffect` 依赖 `locale` — 语言变更时重新从 API 获取日期列表（阶段标签由服务端本地化）
- **自动选中**：挂载时选中今天或最近的未来比赛日
- **自动滚动**：首次渲染时将选中日期滚动到可视区域
- **UI**：横向滚动，箭头导航，阶段色彩日期标签
- **阶段颜色**：小组赛=lime、R32/R16=cyan、QF/SF=magenta、3rd/Final=gold
- **阶段标签**：使用 `stageKey()` + `t()` 实现本地化阶段缩写（小组赛/32强等）
- **i18n**：使用 `useTranslation()` 管理月/星期标签、阶段标签和加载文本
- **依赖**：`Button`（shadcn）、`cn` 工具、`getMatchDates` API（含 timezone 参数）
- **行数**：~260

### `match-cards-grid.tsx` — `MatchCardsGrid`
- **Props**：`selectedDate`、`timezone`（"local" | "host"）
- **数据**：通过 `getMatches({ date, timezone })` 从 API 获取 — 动态、按日期驱动；locale 变更时重新获取（依赖 `locale`）
- **子组件**：`MatchCard`、`CityIconComponent`、`EmptyState`
- **实时数据**：订阅 `useLiveStore` 获取实时比分补丁、助威更新和 WS 状态；挂载时启动 `wsClient`
- **助威投票**：`MatchCard.handleCheer()` 调用 `postCheer(matchId, side)` API，乐观更新 + 失败回滚
- **比赛详情**：卡片点击通过 `onMatchClick` 回调打开 `MatchDetailDialog`（传递 matchId）
- **AI 分析**：通过 `dispatchMatchAnalysis()` 共享辅助函数接线分析流 — 构造请求体、添加上下文消息、关闭弹窗、打开移动端抽屉、启动 SSE 流
- **阶段标签**：使用 `stageKey()` + `t()` 实现本地化阶段徽章；小组赛显示"小组 A"格式
- **功能**：实时比分显示（WS 补丁数据）、焦点战徽章、活动条、球迷助威计（悬停展开）、WS 连接指示器、加载/错误/空状态
- **队伍名称层级**：仅显示一行完整国名（text-lg font-bold），无球队代码，确保对阵双方一目了然
- **API 映射**：`apiMatchToUi()` 将后端 `MatchApiItem` → 前端 `Match` 类型（保留原始 `stage` + `groupLabel` 用于 i18n）
- **i18n**：使用 `useTranslation()` 管理所有可见文本含阶段标签
- **导入类型**：`Match`、`CityIcon` 来自 `@/lib/types`，`LiveScorePatch`、`CheerUpdate` 来自 `@/lib/store`
- **依赖**：`cn` 工具、`lucide-react` 图标（含 Wifi、WifiOff）、`getMatches` + `apiMatchToUi` API、`postCheer` 助威 API、`useLiveStore`、`wsClient`、`MatchDetailDialog`、`dispatchMatchAnalysis`
- **行数**：~551

### `group-standings.tsx` — `GroupStandings`
- **数据**：通过 `getGroups()` 从 API 获取 — 全部 12 组（A-L）积分榜
- **子组件**：`GroupCard`（每组积分卡片）
- **功能**：12 组网格（响应式：1→4 列）、出线区高亮（前 2 名）、组别颜色编码（A-L 循环）、跳转到组详情页
- **UI**：毛玻璃卡片 + 颜色编码表头、shadcn Table、出线指示条
- **i18n**：使用 `useTranslation()` 管理所有可见文本；locale 感知球队名（zh-CN → name_zh）
- **依赖**：`cn` 工具、`lucide-react` 图标、`getGroups` API、shadcn `Table` 组件
- **行数**：~307

### `tournament-bracket.tsx` — `TournamentBracket`
- **数据**：通过 `getBracket()` 从 API 获取 — 完整 BracketTree（R32→R16→QF→SF→3rd→F）
- **子组件**：`BracketCard`、`TeamRow`、`RoundConnector`、`DesktopBracket`、`MobileBracket`
- **比赛详情**：BracketCard 点击通过 `onMatchClick` 回调打开 `MatchDetailDialog`（parseInt 从 string match.id）
- **UI**：6 轮横向滚动 + SVG 连接线（桌面端）、垂直堆叠（移动端）
- **功能**：API 数据获取含加载/错误/重试、TBD 球队显示小组排名标签（如 A1、B2）、赢家金色高亮、LIVE 脉冲、季军赛单独分支
- **响应式**：`hidden md:block` 用于 DesktopBracket，`md:hidden` 用于 MobileBracket
- **颜色**：全部使用语义化主题变量（text-gold、text-accent、bg-primary/20 等）
- **文本**：全部通过 `t()` 国际化
- **导入类型**：`BracketMatch`、`BracketTeam`、`BracketRoundName`、`BracketTree` 来自 `@/lib/types`
- **依赖**：`cn` 工具、`lucide-react` 图标（Trophy、Zap、Loader2、AlertCircle、Medal）、`getBracket` API、`useTranslation` i18n、`MatchDetailDialog`
- **行数**：~430

### `match-detail-dialog.tsx` — `MatchDetailDialog`
- **Props**：`matchId`（number | null）、`open`、`onOpenChange`、`onAnalyzeMatch?: (matchData: MatchDetailData, skillId: string) => void`
- **数据**：弹窗打开时通过 `getMatchById(id)` + `getCheers(matchId)` 从 API 获取
- **实时数据**：合并来自 `useLiveStore` 的实时比分补丁和助威更新
- **AI 分析**：组件挂载时通过 `getAvailableSkills(lang)` 获取可用 Skill 列表；Skill 选择器默认"自动判断"（`recommendedSkillId()`），用户可手动选择；流式状态通过 `useAIChatStore.isStreaming` 读取
- **区块**：比赛头部（队伍+比分+状态）、实时活动条、球迷助威计、比赛事件时间线（上半场/下半场+加时）、比赛统计（进球/红黄牌）、场馆信息、AI 分析区域（Skill 选择器 + 深度分析按钮）
- **队伍名称层级**：与 MatchCard 一致，仅显示一行完整国名（text-lg font-bold）
- **阶段标签**：使用 `stageKey()` + `t()` 实现本地化阶段徽章（小组赛/32强等）
- **赛博朋克风格**：毛玻璃卡片、发光效果、渐变叠加、实时比分的 LED 显示、AI 按钮渐变（from-cyan to-emerald）
- **i18n**：使用 `useTranslation()` 管理所有可见文本（matchDetail + timeline 命名空间）
- **导入类型**：`LiveScorePatch`、`CheerUpdate` 来自 `@/lib/store`，`MatchDetailData` 来自 `match-detail-helpers`，`SkillInfo` 来自 `@/lib/api/match-analysis`
- **依赖**：Dialog、ScrollArea、Separator、Select（shadcn）、`cn`、`lucide-react` 图标（含 Sparkles）、`getMatchById` API、`getCheers` 助威 API、`useLiveStore`、`useAIChatStore`、`usePreferencesStore`、`getAvailableSkills`、`recommendedSkillId`、辅助组件
- **行数**：~555

### `match-detail-helpers.tsx` — MatchDetailDialog 辅助组件 + 类型 + 分析调度
- **导出类型**：`MatchDetailEvent`、`MatchDetailData`（场馆含 `name_zh`、`city_zh`、`country_zh` 字段）
- **组件**：`EventsSection`（按半场分组的事件列表）、`StatRow`（双条统计）、`VenueInfoItem`（标签-值对）
- **函数**：`dispatchMatchAnalysis(matchData, skillId, closeDialog)` — 共享分析流调度器（构造请求体、添加上下文消息、关闭弹窗、仅移动端打开底部抽屉、启动 SSE 流）；桌面端分析直接在右侧面板展示
- **内部**：`EventIcon`（事件类型图标）、`EventLabel`（事件类型 i18n 标签）
- **行数**：~294

### `ai-copilot-panel.tsx` — `AICopilotPanel`
- **状态**：连接到 Zustand `useAIChatStore` + 本地 `input`、`isFocused`、`thinkingCollapsed`、`errorMessage`、`showDisclaimer`、`streamGlow`（流式开始时短暂发光吸引注意力）
- **子组件**：`MiniRadarChart`、`AnalysisCard`、`ThinkingIndicator`、`TypewriterText`、`ThinkingBlock`
- **Markdown 渲染**：所有 AI 助手消息（历史消息、流式响应、思维块）通过 `MarkdownRenderer`（`react-markdown` + `remark-gfm`）渲染为富文本；用户消息保持纯文本
- **特殊消息**：`analysis-context` 类型消息使用 Sparkles 图标 + 渐变边框气泡样式（from-cyan to-lime），与普通用户消息视觉区分
- **数据**：通过 `streamChat()` 来自 `@/lib/api/ai-chat` 的真实 SSE 流式；store 管理消息
- **AI 集成**：通过 fetch+ReadableStream SSE 消费者 POST 到 `/api/ai/chat`；打字机光标效果；可折叠思维块；错误 + 免责声明状态
- **功能**：快捷提示按钮自动发送 AI 请求、流式打字机效果、可折叠推理展示、AnalysisCard（雷达图 + 概率 + 洞察）、自动滚动、欢迎消息种子（跟随 `language` 变化自动重置，仅限无用户消息时）、AbortController 支持
- **i18n**：所有文本通过 `t()`（ai 命名空间）
- **导入类型**：`TeamAnalysis`、`TeamStats` 来自 `@/lib/types`；`ChatMessageItem` 来自 `@/lib/api/ai-chat`
- **依赖**：`Input`、`Button`（shadcn）、`cn`、`lucide-react`、`useAIChatStore`、`usePreferencesStore`、`useTranslation`、`streamChat`、`MarkdownRenderer`
- **行数**：~596

### `ai-copilot-mobile.tsx` — `AICopilotMobile`
- **导出函数**：`openMobileCopilotSheet()` — 供外部组件调用以程序化打开移动端底部抽屉（无需 ref 钻取）
- **状态**：本地 `open`（Sheet 可见性），从 `useAIChatStore` 读取 `isStreaming`
- **组件**：FAB（固定右下角，`lg:hidden`）+ Sheet（底部抽屉，`h-[88vh]`）封装 `AICopilotPanel`
- **功能**：带流式脉冲指示器的 FAB、可访问的 Sheet 含 sr-only 头部、赛博朋克主题渐变 FAB 按钮
- **外部触发**：模块级 `_openSheetFn` 注册 `setOpen(true)`，供 `dispatchMatchAnalysis()` 等外部函数调用
- **i18n**：使用 `t()` 管理 FAB 标签、Sheet 标题/描述（ai 命名空间：fabLabel、sheetTitle、sheetDescription）
- **依赖**：`Sheet`/`SheetContent`/`SheetHeader`/`SheetTitle`/`SheetDescription`（shadcn）、`AICopilotPanel`、`MessageCircle`/`Sparkles`（lucide-react）、`useAIChatStore`、`useTranslation`
- **可见性**：仅在 `lg` 断点以下渲染（FAB 使用 `lg:hidden` class）
- **行数**：~94

## 共享组件

### `components/ui/markdown-renderer.tsx` — `MarkdownRenderer`
- **功能**：将 Markdown 文本渲染为带样式的富文本，专为 AI 聊天消息设计
- **Props**：`content`（Markdown 字符串）、`className`（可选）
- **依赖**：`react-markdown`、`remark-gfm`（GFM 表格、删除线等扩展）
- **样式映射**：所有元素使用项目语义化变量（`text-foreground`、`text-accent`、`bg-secondary`、`border-glass-border` 等）
  - 标题（h1-h3）、段落、有序/无序列表、粗体、斜体
  - 引用块（`border-accent/40` 左边框）
  - 行内代码（`text-accent` + `bg-secondary/50`）、代码块（`bg-secondary/40` + `border-glass-border`）
  - 表格（玻璃边框）、链接（`text-accent`）、分割线
- **使用方**：`AICopilotPanel`（历史消息、流式响应、思维块）

### `lib/flags.tsx` — `TeamFlag` 国旗图片组件
- **功能**：将 FIFA 3 字母代码（如 BRA、USA）映射为 flagcdn.com 上的国旗图片，替代原有 emoji 国旗
- **映射**：内置 FIFA→ISO2 映射（48 支 2026 世界杯队伍）+ 英文名→ISO2 兜底映射（用于 AI 分析等无 code 的场景）
- **CDN**：`https://flagcdn.com/w{size}/{iso2}.webp`，使用 `next/image` + `unoptimized` 模式；`snapToValidWidth()` 将像素宽度向上取整到 CDN 合法宽度（20/40/80/160/320/640/1280）
- **Props**：`code`（FIFA 3 字母代码或英文队名）、`size`（像素，默认 48）、`className`
- **特殊处理**：英格兰 `gb-eng`、苏格兰 `gb-sct`

### `components/ui/dialog.tsx` — Dialog 基础组件（shadcn/ui）
- **遮罩层**：`DialogOverlay` — `bg-black/80`（80% 不透明黑色遮罩，含 fade 动画）
- **内容层**：`DialogContent` — 默认 `bg-background`，可被外部 className 覆盖
- **扩展**：`showCloseButton` prop 控制是否显示右上角关闭按钮
- **使用方**：`MatchDetailDialog` 使用 `glass-card-opaque` 替代默认样式

### `components/theme-provider.tsx`
- `next-themes` 封装（ThemeProvider）。**当前 layout.tsx 中未使用。**

### `components/ui/` — shadcn/ui 基础组件
约 60 个已安装组件。仪表盘中使用的核心组件：
- `button.tsx`、`input.tsx`、`switch.tsx`、`label.tsx`
- `dialog.tsx`（含自定义遮罩层透明度配置）

## 类型定义

类型集中在 `lib/types/` 并从 `@/lib/types` 统一导出。使用 `import type { ... } from "@/lib/types"` 导入。

## i18n 系统（`lib/i18n/`）

### 架构
- **方案**：轻量 React Context（无外部 i18n 库）
- **Provider**：`I18nProvider` 在 `layout.tsx` 中封装应用
- **Hook**：`useTranslation()` → `{ t, locale, setLocale }`
- **持久化**：`localStorage` 键 `worldcup-locale`
- **自动检测**：首次访问读取 `navigator.language`（zh* → zh-CN，其余 → en-US）
- **语言映射**：zh-CN → `document.documentElement.lang = "zh"`，en-US → `"en"`
- **API 同步**：locale 变更时调用 `setApiClientLanguage()`，确保所有 API 请求携带正确的 `lang` 参数和 `Accept-Language` 头

### 语言文件
| 文件 | 语言 | 键数 |
|------|------|------|
| `locales/zh-CN.json` | 简体中文 | 156+ 键，11 个命名空间（header、timeline、match、matchDetail、bracket、ai、footer、groups、stats、teamDetail、common） |
| `locales/en-US.json` | English | 155+ 键，11 个命名空间（与 zh-CN 结构完全一致） |

### 命名空间
| 命名空间 | 键数 | 用途 |
|----------|------|------|
| `header` | 8 | 标题、副标题、时区/视图标签、语言标签（langZh/langEn） |
| `timeline` | 8 | 阶段标签（小组赛/R32/R16/QF/SF/季军赛/决赛/休息日） |
| `match` | 14 | 比赛卡片标签（实时/焦点战/完赛/助威/liveUpdates/disconnected 等） |
| `matchDetail` | 26 | 比赛详情弹窗标签（事件、统计、场馆、助威、AI 分析区域） |
| `bracket` | 15 | 淘汰赛对阵图标签（6 轮、待定、状态） |
| `ai` | 29 | AI 助手面板标签（含 fabLabel、sheetTitle、sheetDescription） |
| `footer` | 4 | 页脚状态栏标签 |
| `groups` | 18 | 小组积分榜标签（标题、表格列、导航、状态） |
| `common` | 22 | 星期、月份、通用消息 |

### 使用方式
```typescript
import { useTranslation } from "@/lib/i18n"

function MyComponent() {
  const { t, locale, setLocale } = useTranslation()
  return <h1>{t("header.title")}</h1>  // "World Cup 2026" 或 "世界杯 2026"
}
```

## API 客户端层（`lib/api-client.ts` + `lib/api/`）

### `lib/api-client.ts` — 核心 fetch 封装
- **导出**：`apiRequest<T>(path, options)`、`buildQueryString(params)`、`setApiClientLanguage(lang)`、`getApiClientLanguage()`、`ApiClientError`
- **配置**：`NEXT_PUBLIC_API_URL` 环境变量（默认：`http://localhost:8000`）
- **功能**：
  - 自动添加基础 URL
  - 从 i18n 状态附加 `Accept-Language` 头（模块级 `currentLang`，通过 `setApiClientLanguage` 更新）
  - 超时支持（默认 15s，AbortController）
  - 解包 `ApiResponse<T>` 信封（直接返回 `data` 字段）
  - 统一错误处理：网络错误、HTTP 状态码（401/403/404/422/429/500/502-504）→ `ApiClientError`
  - `buildQueryString()` 跳过 undefined/null 值

### API 模块（`lib/api/`）
| 模块 | 函数 | 后端端点 |
|------|------|----------|
| `matches.ts` | `getMatchDates(options?)`（含 timezone 参数）、`getMatches(params)`、`getMatchById(id, opts)`、`getLiveMatches(opts)`、`apiMatchToUi(item)` | `GET /api/matches/dates`、`GET /api/matches`、`GET /api/matches/:id`、`GET /api/matches/live` |
| `bracket.ts` | `getBracket(opts)` — 映射后端 VO 字段（`round_name`→`round`、`home_team`→`team1`、`stage`→`round`、`id:int`→`id:string`）；最佳第三名 `from_group` 含 `/` 时显示为 `3rd(A/B/C/D/F)` | `GET /api/bracket` |
| `teams.ts` | `getTeams(params)`、`getTeamByCode(code)` | `GET /api/teams`、`GET /api/teams/:code` |
| `groups.ts` | `getGroups()`、`getGroupDetail(group, opts)` | `GET /api/groups`、`GET /api/groups/:group` |
| `venues.ts` | `getVenues(params)` | `GET /api/venues` |
| `cheers.ts` | `getCheers(matchId)`、`postCheer(matchId, side)` | `GET /api/cheers/:matchId`、`POST /api/cheers/:matchId` |
| `ai-chat.ts` | `streamChat(messages, context, lang, callbacks, signal?)` | `POST /api/ai/chat`（SSE 流式，通过 fetch+ReadableStream） |
| `match-analysis.ts` | `streamMatchAnalysis(body, callbacks, signal?)`、`getAvailableSkills(lang?)` | `POST /api/ai/match-analysis`（SSE 流式）、`GET /api/ai/skills` |

**使用方式**：
```typescript
import { getMatches } from "@/lib/api/matches"
import { setApiClientLanguage } from "@/lib/api-client"

// 从 i18n provider 设置语言
setApiClientLanguage("zh-CN")

// 获取数据 — ApiResponse 信封自动解包
const result = await getMatches({ date: "2026-06-14", page: 1, pageSize: 20 })
// result = { items: Match[], total, page, page_size }
```

| 模块 | 类型 | 用途 |
|------|------|------|
| `lib/types/team.ts` | `Team`、`TeamDetail`、`TeamStanding` | 球队基础结构、API 详情、小组积分行 |
| `lib/types/match.ts` | `Match`、`MatchStatus`、`CityIcon`、`MatchEvent`、`MatchEventType`、`MatchQueryParams` | 比赛卡片数据、事件时间线、API 查询过滤 |
| `lib/types/bracket.ts` | `BracketTeam`、`BracketMatch`、`BracketRound`、`BracketTree`、`BracketRoundName`、`BracketMatchStatus` | 淘汰赛对阵树（R32→F） |
| `lib/types/ai.ts` | `Message`、`MessageRole`、`MessageType`（含 `analysis-context`）、`TeamAnalysis`、`TeamAnalysisSide`（含可选 `code`）、`TeamStats`、`SSEEvent`、`SSEEventType` | AI 聊天消息、分析载荷、SSE 流式 |
| `lib/types/api.ts` | `ApiResponse<T>`、`PaginatedResponse<T>`、`ApiError` | 标准 API 信封类型 |

## 状态管理（`lib/store/`）— Zustand

### 架构
- **方案**：Zustand 存储（轻量，无样板代码）
- **导入**：`import { usePreferencesStore, useMatchesStore, useLiveStore, useAIChatStore } from "@/lib/store"`
- **持久化**：`usePreferencesStore` 使用 `zustand/persist` 中间件（localStorage 键 `worldcup-preferences`）

### 存储注册表
| 存储 | 文件 | 用途 |
|------|------|------|
| `usePreferencesStore` | `preferences.ts` | 用户设置：语言、时区、视图模式、主题（localStorage 持久化） |
| `useMatchesStore` | `matches.ts` | 按日期索引的比赛数据缓存 + 实时比赛，含 TTL 的 fetch 动作 |
| `useLiveStore` | `live.ts` | 实时 WebSocket 状态：连接状态、比分补丁、助威更新 |
| `useAIChatStore` | `ai-chat.ts` | AI 聊天消息、流式缓冲区、待处理分析载荷、分析上下文消息（addAnalysisContextMessage）、推荐技能 ID（recommendedSkillId） |

### 使用方式
```typescript
import { usePreferencesStore } from "@/lib/store"

function MyComponent() {
  const { language, timezone, setLanguage } = usePreferencesStore()
  // language: "zh-CN" | "en-US"
  // timezone: "local" | "host"
  // setLanguage("zh-CN")
}
```

### 关键设计决策
- **偏好设置**通过 `zustand/middleware/persist` 持久化到 localStorage
- **比赛存储**对每个日期有 5 分钟 TTL 缓存，避免重复 API 调用
- **实时存储**镜像 WebSocket 事件，是实时数据的唯一数据源
- **AI 聊天存储**管理流式缓冲区，在流结束时最终化消息

## WebSocket 客户端（`lib/websocket.ts`）

### `wsClient` — 单例 WebSocket 客户端
- **导出**：`wsClient`（WSClient 实例）
- **配置**：`NEXT_PUBLIC_WS_URL` 环境变量（从 `NEXT_PUBLIC_API_URL` 自动推导，将 `http` 替换为 `ws`）
- **端点**：`/ws/live`
- **功能**：
  - 自动连接，指数退避重连（基础 1s，最大 30s，20 次尝试）
  - 将所有后端事件分发到 Zustand `useLiveStore`
  - 订阅/取消订阅特定比赛频道
  - 连接状态在 `useLiveStore.wsStatus` 中跟踪

### 事件映射（后端 → Zustand 实时存储）
| 后端 WSEventType | 前端动作 | 存储方法 |
|------------------|----------|----------|
| `score_update` | 应用比分补丁 | `applyScoreUpdate({ matchId, score1, score2, status, activityLevel })` |
| `match_start` | 设置 status=live，比分=0 | `applyScoreUpdate(...)` |
| `match_end` | 设置 status=finished，最终比分 | `applyScoreUpdate(...)` |
| `activity_update` | 更新活动等级（保留比分） | `applyScoreUpdate(...)` |
| `cheer_update` | 更新助威计数 | `applyCheerUpdate({ matchId, home, away })` |
| `connected` | 应用初始实时比赛载荷 | 批量 `applyScoreUpdate(...)` 每场实时比赛 |
| `ping` | 无操作（浏览器自动响应） | — |
| `bracket_update` | 无操作（预留未来使用） | — |

### 使用方式
```typescript
import { wsClient } from "@/lib/websocket"
import { useLiveStore } from "@/lib/store"

// 启动连接（通常在顶层组件挂载时）
wsClient.start()

// 订阅特定比赛更新
wsClient.subscribeToMatch(42)

// 在组件中读取实时数据
const scorePatch = useLiveStore((s) => s.scoreUpdates[matchId])
const cheerData = useLiveStore((s) => s.cheerUpdates[matchId])
const wsStatus = useLiveStore((s) => s.wsStatus)

// 停止连接（页面卸载时）
wsClient.stop()
```

## CSS 架构（`app/globals.css`）

| 概念 | CSS 变量 / 类 | 用途 |
|------|--------------|------|
| 主色 | `--primary`（`#CCFF00`） | 电子绿，按钮、高亮 |
| 强调色 | `--accent`（`#00F0FF`） | 赛博青，实时指示器 |
| 品红 | `--magenta`（`#FF00E5`） | 半决赛阶段，装饰 |
| 金色 | `--gold`（`#FFD700`） | 焦点战、决赛、高级元素 |
| 毛玻璃卡片 | `.glass-card` | `backdrop-filter: blur(20px)`，40% 透明度 |
| 毛玻璃卡片（不透明） | `.glass-card-opaque` | 95% 不透明度，用于弹窗/对话框防止内容穿透 |
| 毛玻璃边框 | `--glass-border` | `rgba(255,255,255,0.08)` |
| 比分字体 | `.font-score` | Geist Mono，等宽数字 |
| LED 显示 | `.led-display` | 实时比分文字阴影发光 |
| 隐藏滚动条 | `.scrollbar-hide` | 跨浏览器隐藏滚动条 |
