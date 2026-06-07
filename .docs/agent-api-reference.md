# Agent API 参考

> 后端 API 契约文档。完整规格见 `football-web/REQUIREMENTS.md` 第七节。

## 状态：应用工厂 + DI + 工具层 + 种子数据 + 前端 API 客户端 + Redis 基础设施 + 助威服务 + 实时服务 + WebSocket + AI 服务 + AI 控制器 + 爬虫基础设施 + 实时爬虫 + 数据同步 + 调度器 + AI 比赛分析端点 + Skill 列表端点 + 飞书 Bot 集成（推送 + 交互式 AI Bot） 已全部完成

后端脚手架、异常层级、中间件、ORM 模型、Pydantic Schema、Repository、Service、Controller、**应用工厂（main.py）**、**依赖注入（dependencies.py）**、**运行入口（run.py）**、**工具模块（utils/）**、**种子数据流水线**、**前端 API 客户端层**、**Redis 基础设施（app/redis/）**、**助威投票服务/控制器**、**实时服务**、**WebSocket 管理器 + 控制器**、**AI 服务（Deepseek API 客户端含 SSE 流式）**、**AI 控制器（POST /api/ai/chat SSE 端点）**、**爬虫基础设施（BaseScraper + FIFAScraper）**、**实时比分爬虫（LiveScoreScraper）**、**数据同步服务（DataSyncService）**、**调度器（ScraperScheduler）**、**飞书推送服务（FeishuPushService — hook into _broadcast_event）** 和 **飞书交互式 Bot（FeishuBotService — 意图解析 + AI 分析）** 均已实现。
`uvicorn app.main:app --reload` 可正常启动；`/docs` 显示 OpenAPI 所有注册路由。
种子数据：`python -m scripts.seed_data` — 一键初始化（16 座球场、48 支球队、104 场比赛、对阵链接、48 行小组积分）。
前端 API 客户端：`football-web/lib/api-client.ts` + `football-web/lib/api/*.ts` — 类型安全的 fetch 封装，含 `ApiResponse<T>` 解包、语言头、超时和统一错误处理。
Redis：`app/redis/` — 连接池管理器，优雅降级（REDIS_ENABLED=false → 所有操作使用降级方案），通过 `RedisKeys` 类管理键模式。
助威：`app/services/cheer_service.py` + `app/controllers/cheer_controller.py` — Redis HASH 原子计数器含内存降级、基于 IP 的频率限制。
实时：`app/services/live_service.py` — Redis HASH 实时比赛状态（status/score/activity）含内存降级；`MatchService` 自动合并 Redis 实时数据到数据库查询结果；**状态变化时广播 WebSocket 事件**（score_update、match_start、match_end、activity_update、bracket_update）。
WebSocket：`app/services/websocket_manager.py` + `app/controllers/ws_controller.py` — ConnectionManager 单例，支持 connect/disconnect、subscribe/unsubscribe、broadcast/broadcast_to_match；WS /ws/live 端点含初始载荷、心跳 ping 和自动清理。

## 工具层

位于 `app/utils/` 的共享辅助模块，无业务逻辑耦合。

| 模块 | 函数/类 | 说明 |
|------|---------|------|
| `markdown_parser.py` | `MarkdownParser`、`ParsedMatch` | 解析 `data/2026_FIFA_World_Cup_Group_Stage.md` → 72 个结构化 `ParsedMatch` 对象（12 组 × 6 场）。提取：group_label、round_num、match_date、主/客队名（中文）、FIFA 排名。 |
| `timezone.py` | `utc_to_local(utc_dt, target_tz)`、`get_host_city_time(utc_dt, venue_tz)`、`convert_datetime(utc_dt, target_tz, fmt)` | 基于 `zoneinfo` 的纯时区转换（无第三方依赖）。被 MatchService、GroupService、BracketService 使用。 |

**ParsedMatch dataclass 字段**：`group_label`（A-L）、`round_num`（1-3）、`match_date`（date）、`home_team_zh`、`away_team_zh`、`fifa_ranking_home`、`fifa_ranking_away`

## 爬虫基础设施（`app/scraping/`）

### `app/scraping/base_scraper.py` — BaseScraper
- **频率限制**：`asyncio.Semaphore` 限制并发 HTTP 请求为 `SCRAPER_CONCURRENCY`（默认 3）。
- **指数退避重试**：最多 `SCRAPER_RETRY_MAX`（默认 3）次重试，延迟 `2**attempt` 秒，用于瞬态故障。
- **错误层级**：`ScraperError`（基类）→ `ScraperTimeoutError`、`ScraperHTTPError`（含 `status_code`）、`ScraperParseError`。
- **可重试检查**：对 `httpx.TimeoutException`、`httpx.ConnectError` 和 HTTP 5xx 重试。不可重试错误（4xx）立即抛出。
- **结构化日志**：每个请求记录 URL、状态码、耗时和尝试次数。
- **HTTP 客户端**：使用 `httpx.AsyncClient`，懒初始化；支持异步上下文管理器协议。
- **配置**：`SCRAPER_CONCURRENCY`、`SCRAPER_TIMEOUT`、`SCRAPER_RETRY_MAX` 来自 `app.config.settings`。

### `app/scraping/fifa_scraper.py` — FIFAScraper(BaseScraper)
- `scrape_match_schedule()` → `ScrapedSchedule` — 获取 FIFA 赛程页面，提取 `__NEXT_DATA__` JSON，解析比赛列表。
- `scrape_match_result(match_id)` → `ScrapedMatchResult` — 获取单个比赛页面，提取含事件的结果。
- **JSON 提取**：`_extract_next_data()` 使用正则提取 `__NEXT_DATA__` script 标签内容；尝试多个备选 JSON 路径。
- **优雅降级**：当页面结构不匹配时返回空赛程/结果。
- **配置**：`FIFA_SCHEDULE_URL`、`FIFA_MATCH_URL` 来自 `app.config.settings`。

### `app/schemas/scraper_schema.py` — 爬虫数据模型
| 模型 | 字段 | 验证 |
|------|------|------|
| `ScrapedMatch` | external_id, home_team, away_team, kickoff_utc, stage, group_label?, venue_name?, status, home_score?, away_score? | stage ∈ {group, R32, R16, QF, SF, 3rd, F}；status ∈ {upcoming, live, finished, postponed} |
| `ScrapedSchedule` | matches: List[ScrapedMatch], scraped_at, source_url | — |
| `ScrapedLiveEvent` | event_type, minute (≥0), team_side, player_name? | team_side ∈ {home, away} |
| `ScrapedLiveScore` | match_id, home_score (≥0), away_score (≥0), status, activity_level (0-100), events: List[ScrapedLiveEvent] | status ∈ {upcoming, live, finished, postponed} |
| `ScrapedLiveScoreBatch` | matches: List[ScrapedLiveScore], scraped_at, source_url | — |
| `ScrapedEvent` | event_type, minute (≥0), team_side, player_name? | team_side ∈ {home, away} |
| `ScrapedMatchResult` | external_id, status, home_score (≥0), away_score (≥0), events, scraped_at, source_url | status ∈ {upcoming, live, finished, postponed} |

### `app/scraping/live_score_scraper.py` — LiveScoreScraper(BaseScraper)
- `scrape_live_scores()` → `ScrapedLiveScoreBatch` — 获取赛程页面，筛选进行中的比赛，返回含活动等级的已验证实时比分数据。
- **活动等级估算**：`_estimate_activity_level(events, current_minute)` — 基于事件类型权重和比赛分钟数的启发式方法。
- **实时状态检测**：接受 "live"、"in_play"、"inplay"、"halftime"、"1h"、"2h"、"et"、"ht"。
- 复用 `fifa_scraper.py` 中的 `_extract_next_data()`。

### `app/scraping/data_sync.py` — DataSyncService
- `sync_live_scores(batch)` → int — 通过 `LiveService` 同步实时比分到 Redis。返回已同步比赛数量。
- `sync_match_result(result)` → Optional[Match] — 将已完赛比赛结果同步到 SQLite（更新比分、状态、事件）。更新 `LiveService` 以反映完赛状态。
- `sync_group_standings()` → int — 从已完赛小组赛重新计算所有 12 组积分榜。返回更新行数。
- **分布式锁**：`_acquire_lock()` / `_release_lock()` — Redis `SET NX EX` 含 Lua 脚本安全释放（仅删除自己的令牌）。Redis 不可用时降级为 `asyncio.Lock`。
- **锁键**：`RedisKeys.SCRAPER_LOCK`（= `scraper:lock`），TTL：60s。
- **外部 ID 解析**：`_resolve_match_id()` 先查数据库，回退到整数解析。

### `app/scraping/scheduler.py` — ScraperScheduler
- `start()` → None — 启动三个 `asyncio.Task` 周期循环。`SCRAPER_ENABLED=false` 时不执行任何操作。
- `stop()` → None — 通过 `task.cancel()` 取消所有任务，通过 `asyncio.gather(return_exceptions=True)` 等待，记录非 CancelledError 异常。
- **周期任务**：
  - `live_scores`（默认 30s，通过 `SCRAPER_LIVE_INTERVAL` 可配置）— 通过 `LiveScoreScraper` 爬取实时比赛数据，通过 `DataSyncService` 同步到 Redis。当没有比赛进行中时跳过（通过 `LiveService.get_live_matches()` 检查）。
  - `finished_results`（默认 5min，通过 `SCRAPER_FINISHED_INTERVAL` 可配置）— 从数据库查询最近的已完赛比赛，通过 `FIFAScraper` 爬取每场比赛结果，通过 `DataSyncService.sync_match_result()` 持久化比分/事件。单次爬取间隔 2s。
  - `group_standings`（默认 1h，通过 `SCRAPER_GROUP_INTERVAL` 可配置）— 通过 `DataSyncService.sync_group_standings()` 重新计算所有 12 组积分榜。
- **集成**：在 `main.py` 生命周期中 DB 引擎 + Redis 初始化之后启动。接收 `sessionmaker` 工厂用于每个任务的 DB 会话。
- **错误处理**：每个周期运行捕获所有异常，通过 `logging.error` 记录，并在下一个间隔重试。`CancelledError` 传播以实现干净关闭。
- **配置**：间隔从 `app.config.settings` 读取（环境变量可覆盖）：`SCRAPER_LIVE_INTERVAL`、`SCRAPER_FINISHED_INTERVAL`、`SCRAPER_GROUP_INTERVAL`。

## Redis 基础设施（`app/redis/`）

### `app/redis/client.py` — 连接池管理器
- `init_redis_pool()` — 通过 `redis.asyncio` 创建异步连接池；使用 `ping()` 验证。`REDIS_ENABLED=false` 时不执行任何操作。
- `close_redis_pool()` — 优雅关闭；关闭 `Redis` 和 `ConnectionPool`。
- `get_redis() -> Optional[Redis]` — FastAPI `Depends` 提供者；Redis 不可用时返回 `None`。
- `is_redis_available() -> bool` — 下游服务的健康检查。
- 优雅降级：连接失败记录警告，永不阻塞启动。

### `app/redis/keys.py` — 键模式定义
| 常量 | 模式 | 用途 |
|------|------|------|
| `LIVE_MATCH` | `live:match:{match_id}` | 实时比分/状态/活动哈希 |
| `CHEERS_MATCH` | `cheers:match:{match_id}` | 球迷助威计数（home/away）哈希 |
| `WS_CONNECTIONS` | `ws:connections` | 活跃 WebSocket 客户端 ID 集合 |
| `CACHE_GROUPS` | `cache:groups` | 小组积分 JSON 缓存 |
| `CACHE_BRACKET` | `cache:bracket` | 对阵树 JSON 缓存 |
| `SCRAPER_LOCK` | `scraper:lock` | 爬虫分布式锁 |

用法：`RedisKeys.LIVE_MATCH.format(match_id=42)` → `"live:match:42"`

## 服务层

所有 Service 在构造时接收 `AsyncSession`；它们委托给 Repository 并返回纯字典（通过 Pydantic VO 验证）。

| 服务 | 方法 | 说明 |
|------|------|------|
| `TeamService` | `get_all_teams(page, page_size, group, lang)`、`get_team_by_code(code, lang)`、`get_teams_by_group(group_label, lang)` | 支持 `lang="zh"` 将 `name_zh` 提升到 `name` 字段 |
| `VenueService` | `get_all_venues(page, page_size)` | 返回含时区信息的场馆 |
| `MatchService` | `get_match_dates(timezone_name)`、`get_matches(params, timezone_name, lang, page, page_size)`、`get_match_by_id(match_id, timezone_name, lang)`、`get_live_matches(timezone_name, lang)` | 多条件筛选（日期/阶段/小组/球队/状态）含二次内存过滤（时区感知）；通过 `zoneinfo` 进行时区转换，添加 `local_time` 和 `host_time` 字段；`get_match_dates` 返回不同日期及主阶段标签（支持时区分组）；**日期筛选支持时区感知**：传入 `timezone_name` 时按用户本地日期过滤，否则按 UTC；语言感知（为球队提升 `name_zh`，为场馆提升 `name_zh`/`city_zh`/`country_zh`）；**Redis 可用时自动合并实时数据**（status/score/activity_level）到查询结果 |
| `GroupService` | `get_all_groups(lang)`、`get_group_detail(group_label, timezone_name, lang)` | 返回所有 12 组积分榜概览或单组详情含积分榜 + 比赛；积分榜按积分降序、净胜球降序、进球数降序排列；语言感知（提升 `name_zh`）；验证组标签 A-L |
| `BracketService` | `get_full_bracket(lang, timezone_name)`、`get_bracket_by_round(round_name, lang, timezone_name)`、`get_predictions()` | 返回淘汰赛对阵树（R32→R16→QF→SF→3rd→F）按轮次分组；单轮查询；R32 中的 TBD 球队携带 `from_group`/`from_position` 上下文（如"1st Group A"）；预测端点返回第三阶段 AI 集成的占位 |
| `CheerService` | `get_cheers(match_id)`、`vote_cheer(match_id, side, client_ip)` | Redis HASH 计数器（`cheers:match:{id}` 含 `home`/`away` 字段）；通过 pipeline 的 HINCRBY 原子递增；基于 IP 的频率限制（每场比赛+IP 5 分钟冷却）；Redis 不可用时使用类级别内存降级；`_cleanup_expired_rate_limits()` 防止内存无限增长 |
| `LiveService` | `update_match_status(match_id, status)`、`update_score(match_id, home_score, away_score)`、`update_activity(match_id, level)`、`get_live_matches()`、`get_match_live_data(match_id)`、`apply_sync_data(match_id, *, home_score?, away_score?, status?, activity_level?, events?)` | Redis HASH 实时状态（`live:match:{id}` 含 `status`/`home_score`/`away_score`/`activity` 字段）；内存降级；状态/比分变化时的缓存失效标记；MatchService 通过 `_merge_live_data_batch()` 自动合并 Redis 实时数据到查询结果；**状态变化时广播 WebSocket 事件**（MATCH_START/MATCH_END/SCORE_UPDATE/ACTIVITY_UPDATE/BRACKET_UPDATE）；`apply_sync_data()` 是为 DataSyncService 设计的批量更新，单次 Redis 写+读周期 |
| `ConnectionManager` | `connect(websocket, client_id)`、`disconnect(client_id)`、`subscribe(client_id, match_id)`、`unsubscribe(client_id, match_id)`、`broadcast(event_type, data)`、`broadcast_to_match(match_id, event_type, data)`、`get_active_count()` | 通过 `get_manager()` 的模块级单例；进程内活跃 WebSocket 连接注册表；asyncio.Lock 保护状态；自动移除断开连接；支持按比赛订阅频道 |
| `AIService` | `stream_chat(messages, *, context, lang) -> AsyncGenerator[SSEEvent]`、`close()` | Deepseek API 客户端（OpenAI 兼容 `/chat/completions`，model=`deepseek-v4-pro`）；产出 `SSEEvent` 对象：`thinking`（推理增量）、`answer`（内容增量）、`analysis`（检测到分析关键词时的结构化 JSON）、`done`、`error`；使用 `httpx.AsyncClient` 懒初始化；30s 超时；优雅错误处理（速率限制 429、超时、通用错误 → 错误事件，永不抛出）；无 DB 依赖；配置来自 `settings.DEEPSEEK_API_KEY` / `settings.DEEPSEEK_BASE_URL` |
| `PromptBuilder` | `build_system_prompt(lang)`、`build_match_analysis_prompt(match_id, team1, team2, lang)`、`build_custom_match_analysis_prompt(match_id, team1, team2, lang)`、`build_knockout_prompt(match_id, team1, team2, lang)`、`build_chat_context(messages)`、`resolve_skill_id(skill_id, stage)`、`get_available_skills()`、`build_skill_prompt(request: MatchAnalysisRequest)`、`build_championship_prompt(request: ChampionshipAnalysisRequest)` | AI 提示词构建器；`_SKILL_REGISTRY` 模块级字典映射 4 个 skill_id（group_stage_predict、group_stage_round_strategy、knockout_stage_predict、championship_predict）；`build_custom_match_analysis_prompt` 加载 `group_stage_round_strategy.md` skill + `custom_analysis_intro` 模板（R1爆冷猎手/R2稳定猎手/R3终局猎手），用于飞书"定制版"关键词触发场景；`build_championship_prompt` 加载冠亚军策略文件（对 `{simulation_count}` 占位符做动态替换）+ 蒙特卡洛模拟指令（`simulation_count` 从 `request.simulation_count` 读取，动态注入 prompt）→ `[system_msg, user_msg]`；提示词常量抽取至 `app/services/prompts/` 子模块（system_prompts.py、championship_prompts.py）；所有方法为 static；无实例状态 |
| `StatsService` | `get_scorers(lang, limit)` | 从 MatchEventRepository 聚合进球事件，丰富球队信息；返回射手字典列表（rank、player_name、team_code、team_name、team_name_zh、team_flag、goals、assists）；语言感知（提升 name_zh） |

## 控制器层

控制器使用 FastAPI `APIRouter`，通过 `Depends(get_*_service)` 来自 `app/dependencies.py` 进行 DI。所有响应包裹在 `ApiResponse[T]` 中。

| 控制器 | 路由 | 查询参数 |
|--------|------|----------|
| `team_controller` | `GET /api/teams` | `page`、`page_size`、`group`（A-L）、`lang`（en/zh） |
| `team_controller` | `GET /api/teams/{code}/stats` | `timezone`（IANA）、`lang`（en/zh）— 球队资料含积分 + 已完/未完比赛 |
| `team_controller` | `GET /api/teams/{code}` | `lang`（en/zh） |
| `venue_controller` | `GET /api/venues` | `page`、`page_size` |
| `match_controller` | `GET /api/matches` | `date`（YYYY-MM-DD）、`stage`、`group`（A-L）、`team`（code）、`status`、`timezone`（IANA）、`lang`、`page`、`page_size` |
| `match_controller` | `GET /api/matches/dates` | `timezone`（IANA，时区感知日期分组）— 前端自动发送用户本地时区 |
| `match_controller` | `GET /api/matches/live` | `timezone`（IANA）、`lang` |
| `match_controller` | `GET /api/matches/{id}` | `timezone`（IANA）、`lang` |
| `group_controller` | `GET /api/groups` | `lang`（en/zh） |
| `group_controller` | `GET /api/groups/{group}` | `timezone`（IANA）、`lang`（en/zh） |
| `bracket_controller` | `GET /api/bracket` | `timezone`（IANA）、`lang`（en/zh） |
| `bracket_controller` | `GET /api/bracket/predictions` | — |
| `cheer_controller` | `GET /api/cheers/{match_id}` | — |
| `cheer_controller` | `POST /api/cheers/{match_id}` | Body：`{side: "home" \| "away"}`；通过 `X-Forwarded-For` 进行 IP 频率限制 |
| `ws_controller` | `WS /ws/live` | WebSocket：初始载荷（connected + live_matches）、按 matchId subscribe/unsubscribe、30s ping 心跳、断开时自动清理 |
| `ai_controller` | `POST /api/ai/chat` | Body：`ChatRequest`（`messages`、`context?`、`lang`）；SSE 流式响应；事件：`thinking`、`answer`、`analysis`、`done`、`error`；以 `data: [DONE]\n\n` 终止 |
| `ai_controller` | `POST /api/ai/match-analysis` | Body：`MatchAnalysisRequest`（`match_id`、`stage`、`skill_id?`、`home_team`、`away_team`、`score?`、`status`、`events?`、`lang`）；SSE 流式响应，格式与 `/chat` 一致；使用 Skill 推理链构建 prompt |
| `ai_controller` | `POST /api/ai/championship-analysis` | Body：`ChampionshipAnalysisRequest`（`skill_id?`、`simulation_count`（默认 2000，范围 100-10000）、`lang`）；SSE 流式响应；加载冠亚军预测策略（蒙特卡洛模拟可自定义推演次数），输出 TOP 20 决赛场景及概率 |
| `ai_controller` | `GET /api/ai/skills` | 返回 `ApiResponse<List<SkillInfo>>`；无数据库查询，从内存 `_SKILL_REGISTRY` 返回；含 3 个 Skill：group_stage_predict、knockout_stage_predict、championship_predict |
| `stats_controller` | `GET /api/stats/scorers` | `lang`（en/zh）、`limit`（1-100，默认 50） |

> 依赖注入集中在 `app/dependencies.py`：
> - `get_db` — 产出 `AsyncSession` 含自动 commit/rollback
> - `get_language` — 从查询参数或 `Accept-Language` 头提取 lang
> - `get_team_service`、`get_match_service`、`get_venue_service`、`get_group_service`、`get_bracket_service`、`get_ai_service` — 服务工厂函数
> - `get_redis`（来自 `app/redis/client.py`）— 返回 `Optional[Redis]`（Redis 不可用时为 `None`）
> 引擎生命周期由 `main.py` lifespan 管理（启动时初始化，关闭时释放）。
> Redis 连接池生命周期也由 `main.py` lifespan 管理（启动时 init_redis_pool，关闭时 close_redis_pool）。

## Repository 层

所有 Repository 继承自 `BaseRepository[T]`（含分页的泛型 CRUD）。
每个 Repository 在构造时接收 `AsyncSession`；调用方控制会话生命周期。

| Repository | 额外方法 | 说明 |
|------------|----------|------|
| `TeamRepository` | `get_by_code(code)`、`get_by_group(group_label)` | code 不存在时抛出 `NotFoundError` |
| `MatchRepository` | `get_by_date(date)`、`get_by_stage(stage)`、`get_by_status(status)`、`get_live_matches()`、`get_bracket_matches()`、`get_by_group_label(group)`、`get_by_team_code(code)`、`get_match_dates()` | 除 `get_live_matches` / `get_bracket_matches` / `get_match_dates` 外均分页 |
| `VenueRepository` | —（仅基础 CRUD） | |
| `GroupRepository` | `get_by_group_label(group)`（排序：积分降序、净胜球降序、进球数降序）、`get_group_matches(group)` | 返回小组的积分榜和比赛 |
| `MatchEventRepository` | `get_by_match(match_id)`（按分钟升序）、`get_scorers_leaderboard(limit)`（按球员聚合进球数含球队信息） | |

**MatchEventRepository.get_scorers_leaderboard**：聚合每个球员的进球事件（`goal`、`penalty`），通过 Match → Team 关联解析球队信息（code、name、name_zh、flag）。返回行包含：player_name、goals、team_code、team_name、team_name_zh、team_flag。按进球数降序排列。

**BaseRepository[T] 方法**：`get_by_id`、`get_by_id_optional`、`get_all(page, page_size, filters, order_by)`、`create(data)`、`update(entity_id, data)`、`delete(entity_id)`

## 数据库结构（5 张表）

所有模型使用 SQLAlchemy 2.0 `Mapped[]` 类型注解和 `mapped_column()`。

| 表 | 主键 | 唯一列 | 外键 |
|----|------|--------|------|
| `teams` | id | name、code | — |
| `venues` | id | — | — |
| `matches` | id | external_id | home_team_id→teams、away_team_id→teams、venue_id→venues、next_match_id→matches(self) |
| `group_standings` | id | team_id | team_id→teams |
| `match_events` | id | — | match_id→matches |

所有表包含 `TimestampMixin` 列：`created_at`、`updated_at`（自动管理）。

## 统一响应信封

所有端点返回包裹在以下格式中的响应：

```json
{
  "code": 200,
  "data": <T | null>,
  "message": "success"
}
```

错误响应遵循相同格式，使用适当的 HTTP 状态码。
异常映射：`NotFoundError→404`、`ValidationError→422`、`BusinessError→400`、`ExternalServiceError→502`、未处理→500。

## 已实现的 API 结构

```
/api
├── /matches
│   ├── GET /                    # 比赛列表（筛选：date、stage、group、team、status）
│   ├── GET /dates               # 所有比赛日期及阶段标签
│   ├── GET /:id                 # 单场比赛详情
│   └── GET /live                # 当前进行中的比赛
├── /bracket
│   ├── GET /                    # 完整淘汰赛对阵树
│   └── GET /predictions         # AI 对阵预测
├── /teams
│   ├── GET /                    # 所有球队
│   ├── GET /:code               # 球队详情
│   └── GET /:code/stats         # 球队统计
├── /groups
│   ├── GET /                    # 所有小组积分榜
│   └── GET /:group              # 单组（积分榜 + 比赛）
├── /venues
│   └── GET /                    # 场馆列表（含时区信息）
├── /cheers
│   ├── GET /:matchId            # 比赛球迷投票数据
│   └── POST /:matchId           # 提交球迷投票
├── /ai
│   ├── POST /chat                    # AI 聊天（SSE 流式）
│   ├── POST /match-analysis          # AI 比赛分析（SSE 流式，Skill 推理链驱动）
│   ├── POST /championship-analysis   # AI 冠亚军预测（SSE 流式，蒙特卡洛模拟）
│   └── GET  /skills                  # AI 分析 Skill 列表（从内存注册表返回）
├── /stats
│   └── GET /scorers              # 射手榜
└── /ws
    └── /live                    # WebSocket 实时事件
```

## 关键数据模型（来自 REQUIREMENTS.md）

完整请求/响应示例和字段定义见 `football-web/REQUIREMENTS.md`。

### 比赛响应结构
```typescript
interface MatchResponse {
  date: string
  matches: Array<{
    id: number
    stage: string
    round: number
    status: "upcoming" | "live" | "finished"
    isBigMatch: boolean
    activityLevel: number
    team1: { name: string; code: string; flag: string; fifaRanking: number }
    team2: { name: string; code: string; flag: string; fifaRanking: number }
    score: { team1: number; team2: number } | null
    localTime: string
    hostTime: string
    venue: string
    hostCity: string
    hostCityTimezone: string
  }>
}
```

### 对阵图响应结构
```typescript
interface BracketResponse {
  rounds: Array<{
    name: string
    shortName: "R32" | "R16" | "QF" | "SF" | "3rd" | "F"
    matches: Array<{
      id: string
      position: number
      status: "upcoming" | "live" | "completed"
      team1: BracketTeam
      team2: BracketTeam
      nextMatchId: string
      venue: string
      matchTime: string
    }>
  }>
}
```

### AI 比赛分析（SSE 流）— 已实现

```
POST /api/ai/match-analysis
Body: MatchAnalysisRequest {
    match_id: int (必填)
    stage: str (必填, "group" | "R32" | "R16" | "QF" | "SF" | "3rd" | "F")
    skill_id?: str (可选, 不传则根据 stage 自动推断)
    home_team: TeamBrief { name, name_zh, code, flag }
    away_team: TeamBrief { name, name_zh, code, flag }
    home_score?: int | null
    away_score?: int | null
    status: str (必填, "upcoming" | "live" | "finished")
    group_label?: str (A-L, 仅小组赛)
    round?: str
    match_day?: int
    events?: Array<MatchEventBrief>
    lang: str (必填, "zh-CN" | "en-US")
}
Response: SSE 流 (text/event-stream) — 与 /api/ai/chat 格式一致

GET /api/ai/skills
Response: ApiResponse<Array<SkillInfo>>
    SkillInfo { skill_id, name, name_zh, description, description_zh, applicable_stages }
```

### AI 冠亚军预测（SSE 流）— 已实现

```
POST /api/ai/championship-analysis
Body: ChampionshipAnalysisRequest {
    skill_id?: str (可选, 默认 "championship_predict")
    simulation_count?: int (可选, 默认 2000, 范围 100-10000)
    lang: str (必填, "zh-CN" | "en-US")
}
Response: SSE 流 (text/event-stream) — 与 /api/ai/chat 格式一致
- 加载 skills/冠亚军分析.md 策略文件（7 大核心预测策略）
- 系统指令要求模拟 N 次比赛（用户可配置，遵循真实赛程时间线）
- 输出 TOP 20 决赛场景及概率
```

### AI 聊天（SSE 流）— 已实现
```
POST /api/ai/chat
Body: { messages: Array<{role, content}>, context?: {currentView, selectedDate, timezone}, lang: "zh-CN" | "en-US" }
Response: SSE 流 (text/event-stream)
  data: {"type": "thinking", "content": "..."}    # 推理增量
  data: {"type": "answer", "content": "..."}       # 内容增量
  data: {"type": "analysis", "data": {...}}        # 结构化球队分析
  data: {"type": "error", "content": "..."}        # 错误消息
  data: {"type": "done"}                           # 流完成
  data: [DONE]                                     # 终止标记
```

### WebSocket 事件
| 事件 | 数据 |
|------|------|
| `score_update` | `{matchId, team, score, event}` |
| `match_start` | `{matchId, status}` |
| `match_end` | `{matchId, status, score}` |
| `activity_update` | `{matchId, activityLevel}` |
| `bracket_update` | `{matchId, winner, nextMatchId}` |

## 飞书 Bot 集成 — 已实现

### 配置（`app/config.py` 新增字段）

| 变量 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `FEISHU_APP_ID` | str | "" | 飞书应用 App ID |
| `FEISHU_APP_SECRET` | str | "" | 飞书应用 App Secret |
| `FEISHU_VERIFY_TOKEN` | str | "" | Webhook 事件验证 Token |
| `FEISHU_ENCRYPT_KEY` | str | "" | 可选，事件加密密钥 |
| `FEISHU_ENABLED` | bool | False | 飞书功能总开关 |
| `FEISHU_PUSH_ENABLED` | bool | False | Phase 1：推送通知开关 |
| `FEISHU_BOT_ENABLED` | bool | False | Phase 3：交互式 Bot 开关 |
| `FEISHU_CHAT_ID` | str | "" | 推送目标群聊 ID |

计算属性：`feishu_configured` → bool（App ID + App Secret 均非空）

### Phase 1：比赛事件推送

**架构**：`LiveService._broadcast_event()` → `FeishuPushService.handle_event()` → `FeishuCardBuilder` → `FeishuClient.send_card_message()`

| WSEventType | 飞书卡片 | 防抖 |
|---|---|---|
| `MATCH_START` | `build_match_start_card` — 开赛通知（队伍+场馆+阶段） | 60s |
| `SCORE_UPDATE` | `build_score_update_card` — 进球/比分更新 | 10s |
| `MATCH_END` | `build_match_end_card` — 比赛结果（最终比分+关键事件） | 60s |

`ACTIVITY_UPDATE`、`CHEER_UPDATE`、`BRACKET_UPDATE` 被忽略（太频繁或被 MATCH_END 覆盖）。

### Phase 3：交互式 Bot

**端点**：
```
POST /api/feishu/webhook  — 飞书事件回调（URL 验证 challenge + im.message.receive_v1 消息分发）
GET  /api/feishu/health   — 飞书集成状态检查（enabled/push_enabled/bot_enabled/configured/chat_id_set）
```

**意图解析**（`FeishuBotService._parse_intent`）：
| 意图 | 中文关键词 | 英文关键词 | 动作 |
|------|-----------|-----------|------|
| `today_matches` | 今天、今日、赛程 | today, schedule | 查询当日比赛 |
| `match_analysis` | 分析 + vs/对 | analyze + vs | AI 对阵分析 |
| `match_analysis`（定制版） | 定制版 + 分析 + vs/对 | custom + analyze + vs | AI 轮次策略分析（R1爆冷猎手/R2稳定猎手/R3终局猎手） |
| `champion_predict` | 冠军、预测冠军 | champion, predict | AI 冠军预测 |
| `match_query` | 队名子串 | team name | 查询队伍比赛 |
| `general_chat` | 兜底 | fallback | AI 通用对话 |

**`custom_strategy` 标志**：`FeishuIntentResult` 新增 `custom_strategy: bool` 字段。由专用正则 `_CUSTOM_ANALYSIS_PATTERN` 优先匹配"定制版"前缀（如"定制版分析韩国对战捷克"），命中后 `custom_strategy=True`，`handle_message()` 将此标志透传至 `_handle_match_analysis()`，后者调用 `PromptBuilder.build_custom_match_analysis_prompt()` 加载 `group_stage_round_strategy.md` skill 替代标准 `build_match_analysis_prompt()`。意图解析优先级：定制版正则 → 标准分析正则 → 关键词匹配 → GENERAL_CHAT。

**AI 集成**：收集 `AIService.stream_chat()` 全部 answer 事件 → `build_ai_analysis_card()` → `FeishuClient.reply_message()`（一次性发送完整卡片，非流式）。`match_analysis` 意图使用 `build_system_prompt()` + 自然语言分析请求（非结构化 MatchAnalysisRequest），避免飞书纯文本场景下 TeamBrief 校验失败。

**依赖注入**：`_dispatch_bot_message` 通过 `get_shared_feishu_client()` 复用单例 `FeishuClient`；通过 `_session_factory()` 创建临时 `MatchService`（async with 管理 session 生命周期），使 `today_matches` 和 `match_query` 意图可正常查询比赛数据。

**Token 管理**：`FeishuClient.get_tenant_token()` — Redis 缓存 7000s，内存兜底，401 自动刷新重试。
