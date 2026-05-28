# Agent 文件导航

> 按用途快速定位代码文件。

## 根目录

```
ai_WorldCup/
├── CLAUDE.md                 # 工程规范（最高优先级）
├── prompt.md                 # Ralph Agent 循环指令
├── prd.json                  # Story 追踪器（分支 + story 通过标记）
├── progress.txt              # Ralph 执行进度日志
├── archive.js                # 未知工具脚本
├── ralph.sh                  # Ralph Agent Shell 入口
├── .claudeignore             # Claude 忽略规则
├── .docs/                    # 本文档目录
├── data/                     # 赛事原始数据
├── skills/                   # AI 预测技能定义
├── football-web/             # Next.js 前端（主应用）
└── football-server/          # 后端（FastAPI + SQLite + Redis）
```

## football-web/ — 前端（Next.js 16 + React 19）

```
football-web/
├── app/
│   ├── layout.tsx            # 根布局（暗色主题，Geist 字体，Analytics）
│   ├── page.tsx              # 单页仪表盘（默认视图：时间线；所有状态在此管理，小组赛快捷入口，移动端 AI 助手 FAB+Sheet，AI 侧边栏可拖拽缩放 min=340px max=33.33vw）
│   ├── globals.css           # CSS 变量、动画、毛玻璃工具类（.glass-card 40%透明 / .glass-card-opaque 95%不透明用于弹窗）
│   └── groups/
│       ├── page.tsx          # 小组赛总览页（12 组积分榜网格，返回时间线导航）
│       └── [group]/
│           └── page.tsx      # 单组详情页（积分榜 + 比赛列表）
├── bracket/
│   └── page.tsx              # 独立全屏淘汰赛对阵图页面
├── stats/
│   └── page.tsx              # 数据中心页（射手榜 + 比赛统计）
├── teams/
│   └── [code]/
│       └── page.tsx          # 球队详情页（球队资料 + 小组积分 + 已完/未完比赛）
├── components/
│   ├── dashboard/
│   │   ├── header.tsx        # 顶栏（语言切换 + 时区 + 视图模式切换，支持 i18n）
│   │   ├── date-timeline.tsx # 横向日期选择器（6月11日–7月19日）
│   │   ├── match-cards-grid.tsx  # 比赛卡片列表 + 球迷助威 + 实时 WS 比分/助威集成 + 在线连接指示器 + 点击打开比赛详情弹窗
│   │   ├── match-detail-dialog.tsx # 比赛详情弹窗（队伍+比分、事件时间线、统计数据、助威、场馆信息）— 赛博朋克毛玻璃风格
│   │   ├── match-detail-helpers.tsx # 比赛详情辅助组件 + 类型（EventsSection、StatRow、VenueInfoItem、EventIcon/Label）
│   │   ├── group-standings.tsx   # 小组积分榜网格（12 组 A-L，出线区高亮）
│   │   ├── tournament-bracket.tsx # 完整6轮淘汰赛对阵图（R32→R16→QF→SF→3rd→F，API 驱动）+ 点击打开比赛详情
│   │   ├── ai-copilot-panel.tsx   # AI 聊天侧边栏（真实 SSE 流式、打字机效果、思维块、分析卡片、Zustand 存储）
│   │   └── ai-copilot-mobile.tsx  # 移动端 AI 助手 — FAB 入口 + Sheet 底部抽屉（lg 断点以下可见）
│   ├── stats/
│   │   ├── scorers-table.tsx    # 射手榜表格（按进球/助攻排序，赛博朋克毛玻璃卡片，前3名高亮）
│   │   └── match-stats-card.tsx # 比赛统计卡片（未开/进行中/已完计数 + 进度条）
│   ├── theme-provider.tsx    # next-themes 封装（当前布局未使用）
│   └── ui/                   # shadcn/ui 基础组件（约 60 个）
├── hooks/
│   ├── use-mobile.ts         # 移动端断点 Hook
│   └── use-toast.ts          # Toast Hook
├── lib/
│   ├── utils.ts              # cn() 工具函数（clsx + tailwind-merge）
│   ├── api-client.ts         # 核心 fetch 封装：基础 URL、Accept-Language、ApiResponse<T> 解包、错误处理、查询字符串构建
│   ├── websocket.ts          # WebSocket 客户端单例（自动连接/重连、事件分发到 Zustand 实时存储）
│   ├── i18n/                 # 国际化基础设施
│   │   ├── index.ts          # 统一导出（I18nProvider、useI18n、useTranslation、类型）
│   │   ├── context.tsx       # I18nProvider（React Context：locale 状态、t() 函数、localStorage 持久化 + API 语言同步 + locale 切换时存储缓存失效）
│   │   ├── use-translation.ts # useTranslation Hook — 轻量封装，暴露 { t, locale, setLocale }
│   │   ├── types.ts          # Locale 联合类型 + LocaleMessages 接口（镜像 JSON 结构）
│   │   └── locales/
│   │       ├── zh-CN.json    # 中文翻译（155+ 键，11 个命名空间）
│   │       └── en-US.json    # 英文翻译（155+ 键，与 zh-CN 完全对齐）
│   ├── api/                  # API 模块函数（每个后端资源一个文件）
│   │   ├── matches.ts        # getMatchDates(options?)（含 timezone 参数）、getMatches(params)、getMatchById(id)、getLiveMatches()、apiMatchToUi()
│   │   ├── bracket.ts        # getBracket() — 包含后端→前端字段映射层（round_name→round、home_team→team1 等）
│   │   ├── teams.ts          # getTeams(params)、getTeamByCode(code)、getTeamStats(code) — 球队详情含积分 + 比赛
│   │   ├── groups.ts         # getGroups()、getGroupDetail(group)
│   │   ├── venues.ts         # getVenues(params)
│   │   ├── cheers.ts         # getCheers(matchId)、postCheer(matchId, side)
│   │   ├── stats.ts          # getScorers(params) — 射手榜数据
│   │   └── ai-chat.ts        # streamChat() SSE 消费者（fetch+ReadableStream，POST /api/ai/chat）
│   ├── store/                # Zustand 全局状态存储
│   │   ├── index.ts          # 统一导出所有存储
│   │   ├── preferences.ts    # 用户偏好（语言、时区、视图模式、主题）— localStorage 持久化
│   │   ├── matches.ts        # 比赛数据缓存（按日期 + 实时比赛）含 fetch 动作 + TTL + locale 切换时 invalidateAll()
│   │   ├── live.ts           # 实时 WebSocket 状态（比分、助威更新、WS 连接状态）— 由 websocket.ts 事件驱动
│   │   └── ai-chat.ts        # AI 聊天消息 + 流式状态（内容缓冲区、分析载荷）
│   └── types/                # 共享 TypeScript 类型定义
│       ├── index.ts          # 统一导出
│       ├── team.ts           # Team、TeamDetail、TeamStanding
│       ├── match.ts          # Match、MatchStatus、MatchEvent、MatchQueryParams、CityIcon、MatchDateInfo
│       ├── bracket.ts        # BracketTeam、BracketMatch、BracketRound、BracketTree、BracketRoundName
│       ├── ai.ts             # Message、TeamAnalysis、TeamStats、SSEEvent
│       └── api.ts            # ApiResponse<T>、PaginatedResponse<T>、ApiError
├── styles/
│   └── globals.css           # 重复/备选全局样式（需确认是否仍需要）
├── package.json              # 依赖（next 16、recharts、date-fns、zod 等）
├── components.json           # shadcn/ui 配置（new-york 风格，RSC 启用）
├── tsconfig.json             # TypeScript 配置
├── next.config.mjs           # Next.js 配置
└── postcss.config.mjs        # PostCSS 配置
```

## data/ — 赛事数据

```
data/
├── 2026_FIFA_World_Cup_Group_Stage.md  # 12 组 × 6 场（共 72 场），结果待定
└── 2022_FIFA_World_Cup_Results.md      # 卡塔尔 2022 结果（64 场，中文）
```

## skills/ — AI 预测提示词

```
skills/
├── README.md                     # Skills 概览
├── group_stage_predict.md        # 小组赛预测 6 步推理
└── knockout_stage_predict.md     # 淘汰赛预测 5 步推理
```

## football-server/ — 后端（FastAPI + SQLite + Redis）

```
football-server/
├── pyproject.toml               # 项目元数据 + 所有核心依赖
├── alembic.ini                  # Alembic 配置（数据库 URL 来自 app.config，日志）
├── .env.example                 # 环境变量模板
├── .gitignore                   # Python/venv/db 忽略规则
├── run.py                       # Uvicorn 入口（python run.py 或 python run.py --prod）
├── alembic/
│   ├── env.py                   # 异步迁移运行器（读取 settings.DATABASE_URL）
│   ├── script.py.mako           # 迁移脚本模板
│   └── versions/
│       ├── 001_initial_schema.py  # 初始迁移：5 张表 + FK 关系
│       └── 002_venue_zh_fields.py # 为 venues 表添加 name_zh、city_zh、country_zh 字段
├── app/
│   ├── __init__.py              # 包初始化（空）
│   ├── config.py                # Pydantic Settings：所有环境变量及默认值（含 REDIS_URL、REDIS_ENABLED、SCRAPER_*、爬虫间隔）
│   ├── main.py                  # FastAPI 应用工厂（生命周期：DB + Redis 初始化/关闭，ScraperScheduler 启动/停止，中间件，路由，/docs）
│   ├── dependencies.py          # DI 提供者：get_db、get_*_service、get_ai_service、get_language；Redis DI 通过 app.redis.get_redis
│   ├── exceptions/
│   │   ├── __init__.py          # 统一导出所有异常类
│   │   └── exceptions.py        # AppException 层级（NotFound、Validation、Business、ExternalService）
│   ├── middleware/
│   │   ├── __init__.py          # 统一导出所有中间件类
│   │   ├── error_handler.py     # 全局异常 → ApiResponse {code, data, message} 中间件
│   │   ├── cors.py              # CORS 中间件（来源来自配置）
│   │   └── logging.py           # 请求日志中间件（method/path/status/duration）
│   ├── models/
│   │   ├── __init__.py          # 统一导出所有模型类 + Base
│   │   ├── base.py              # DeclarativeBase + TimestampMixin（created_at、updated_at）
│   │   ├── team.py              # Team 模型（48 支球队，code/name UNIQUE）
│   │   ├── venue.py             # Venue 模型（16 座球场，含时区信息）
│   │   ├── match.py             # Match 模型（104 场赛程，FK→Team/Venue/self）
│   │   ├── group_standing.py    # GroupStanding 模型（48 行，FK→Team UNIQUE）
│   │   └── match_event.py       # MatchEvent 模型（进球/红黄牌/换人，FK→Match）
│   ├── repositories/
│   │   ├── __init__.py          # 统一导出所有 Repository 类
│   │   ├── base.py              # BaseRepository[T] 泛型 CRUD（get_by_id、get_all、create、update、delete）
│   │   ├── team_repo.py         # TeamRepository：get_by_code、get_by_group
│   │   ├── match_repo.py        # MatchRepository：get_by_date(支持timezone)、get_by_stage、get_by_status、get_live_matches、get_bracket_matches、get_by_group_label、get_by_team_code、get_match_dates(支持timezone)
│   │   ├── venue_repo.py        # VenueRepository：仅继承基础 CRUD
│   │   ├── group_repo.py        # GroupRepository：get_by_group_label（按积分排序）、get_group_matches
│   │   └── match_event_repo.py  # MatchEventRepository：get_by_match（按分钟排序）
│   ├── services/
│   │   ├── __init__.py          # 统一导出所有 Service 类
│   │   ├── ai_service.py        # AIService：Deepseek API 客户端（stream_chat AsyncGenerator → SSEEvent 对象：thinking/answer/analysis/done/error，30s 超时，优雅错误处理）
│   │   ├── prompt_builder.py    # PromptBuilder：build_system_prompt、build_match_analysis_prompt、build_knockout_prompt、build_chat_context、resolve_skill_id、get_available_skills、build_skill_prompt、_format_match_context（_SKILL_REGISTRY 注册表，双语 zh-CN/en-US，读取 skills/ markdown）
│   │   ├── team_service.py      # TeamService：get_all_teams、get_team_by_code、get_teams_by_group、get_team_stats（支持 lang + timezone）
│   │   ├── venue_service.py     # VenueService：get_all_venues（分页）
│   │   ├── match_service.py     # MatchService：get_match_dates、get_matches（多条件筛选 + Redis 实时合并）、get_match_by_id（含事件 + Redis 实时）、get_live_matches（Redis 实时合并）；使用共享 app.utils.timezone
│   │   ├── group_service.py     # GroupService：get_all_groups（12 组积分榜）、get_group_detail（积分榜 + 比赛）；支持 lang + timezone（共享 utils）
│   │   ├── bracket_service.py   # BracketService：get_full_bracket（R32→F 树形结构）、get_bracket_by_round、get_predictions（TBD 占位）；使用共享 app.utils.timezone
│   │   ├── cheer_service.py     # CheerService：get_cheers、vote_cheer（Redis HASH + 内存降级、IP 频率限制）
│   │   ├── stats_service.py     # StatsService：get_scorers（从 MatchEventRepository 聚合射手榜）
│   │   ├── live_service.py      # LiveService：update_match_status、update_score、update_activity、get_live_matches、get_match_live_data、apply_sync_data（Redis HASH + 内存降级、缓存失效、状态变化时 WebSocket 广播）
│   │   └── websocket_manager.py # ConnectionManager：connect/disconnect、subscribe/unsubscribe、broadcast/broadcast_to_match、get_manager 单例
│   ├── controllers/
│   │   ├── __init__.py          # 统一导出所有路由器
│   │   ├── ai_controller.py    # POST /api/ai/chat + POST /api/ai/match-analysis（SSE 流式：PromptBuilder + AIService.stream_chat → StreamingResponse）+ GET /api/ai/skills（SkillInfo 列表）
│   │   ├── team_controller.py   # GET /api/teams、GET /api/teams/:code/stats、GET /api/teams/:code（使用 get_team_service DI）
│   │   ├── venue_controller.py  # GET /api/venues（使用 get_venue_service DI）
│   │   ├── match_controller.py  # GET /api/matches、/dates、/live、/:id（使用 get_match_service DI）
│   │   ├── group_controller.py  # GET /api/groups、/:group（使用 get_group_service DI）
│   │   ├── bracket_controller.py # GET /api/bracket、/predictions（使用 get_bracket_service DI）
│   │   ├── cheer_controller.py  # GET /api/cheers/:matchId、POST /api/cheers/:matchId（IP 频率限制投票）
│   │   ├── stats_controller.py  # GET /api/stats/scorers（射手榜，使用 StatsService DI）
│   │   └── ws_controller.py     # WS /ws/live（WebSocket 端点：初始载荷、subscribe/unsubscribe、ping/pong 心跳）
│   ├── redis/
│   │   ├── __init__.py          # 统一导出 RedisKeys、get_redis、init_redis_pool、close_redis_pool、is_redis_available
│   │   ├── client.py            # Redis 连接池（init_redis_pool、close_redis_pool、get_redis DI、is_redis_available）
│   │   └── keys.py              # RedisKeys 命名空间类（LIVE_MATCH、CHEERS_MATCH、WS_CONNECTIONS、CACHE_GROUPS、CACHE_BRACKET、SCRAPER_LOCK）
│   ├── utils/
│   │   ├── __init__.py          # 统一导出 MarkdownParser、utc_to_local、get_host_city_time
│   │   ├── markdown_parser.py   # MarkdownParser：解析 data/*.md → list[ParsedMatch]（72 场小组赛赛程）
│   │   └── timezone.py          # utc_to_local、get_host_city_time、convert_datetime（基于 zoneinfo）
│   └── schemas/
│       ├── __init__.py          # 统一导出所有 Schema 类
│       ├── common.py            # ApiResponse[T] + PaginatedResponse[T] 泛型信封
│       ├── team_schema.py       # TeamCreate/TeamUpdate DTO + TeamResponse/TeamListResponse/TeamStatsResponse VO（积分 + 比赛 VO）
│       ├── match_schema.py      # MatchQueryParams DTO + MatchResponse/MatchDetailResponse/MatchEventResponse VO
│       ├── venue_schema.py      # VenueResponse VO
│       ├── group_schema.py      # GroupStandingResponse + GroupDetailResponse VO
│       ├── bracket_schema.py    # BracketTeam/Match/Round/TreeResponse VO（支持 TBD）
│       ├── cheer_schema.py      # CheerVoteRequest DTO + CheerResponse VO
│       ├── stats_schema.py      # ScorerItem VO（排名、球员名、球队信息、进球、助攻）
│       ├── ai_schema.py         # ChatRequest DTO + SSEEvent + TeamAnalysisResponse VO + MatchAnalysisRequest DTO + TeamBrief/MatchEventBrief/SkillInfo VO
│       ├── ws_schema.py         # WSEventType 枚举 + WSMessage VO
│       └── scraper_schema.py   # ScrapedMatch/Schedule/LiveScore/LiveScoreBatch/Event/LiveEvent/MatchResult VO 用于爬虫数据验证
├── scraping/                    # 网页爬虫基础设施
│   ├── __init__.py              # 统一导出 BaseScraper、FIFAScraper、LiveScoreScraper、DataSyncService、ScraperScheduler
│   ├── base_scraper.py          # BaseScraper：频率限制（asyncio.Semaphore）、指数退避重试（最大3次）、结构化日志、错误层级
│   ├── fifa_scraper.py          # FIFAScraper(BaseScraper)：scrape_match_schedule()、scrape_match_result(match_id)；从 FIFA.com 页面提取 __NEXT_DATA__ JSON
│   ├── live_score_scraper.py    # LiveScoreScraper(BaseScraper)：scrape_live_scores() → ScrapedLiveScoreBatch；活动等级启发式估算
│   ├── data_sync.py             # DataSyncService：sync_live_scores、sync_match_result、sync_group_standings；Redis 分布式锁（scraper:lock）
│   └── scheduler.py             # ScraperScheduler：周期任务编排（实时 30s、已完赛 5min、小组积分 1h）；SCRAPER_ENABLED=true 时在 main.py 生命周期中启动
├── scripts/                     # 数据库种子脚本
│   ├── __init__.py              # 包初始化
│   ├── seed_data.py             # 一键初始化编排（seed_venues→teams→matches→bracket→standings）
│   ├── generate_bracket.py      # 对阵图验证 + R32 小组出线映射
│   ├── seed_teams.py            # 种子 48 支球队（按 code 幂等 upsert）
│   ├── team_data.py             # 48 支球队数据（双语、FIFA 排名、大洲）
│   ├── seed_venues.py           # 种子 16 座球场（按 name 幂等 upsert）
│   ├── venue_data.py            # 16 座球场数据（城市、国家、IANA 时区、容量 + 中文翻译）
│   └── seed_matches.py          # 种子 104 场比赛（真实 FIFA 2026 开球时间 + 场馆、对阵链接、TBD 占位球队）
└── scalable-beaming-riddle.md   # 后端架构方案
```
