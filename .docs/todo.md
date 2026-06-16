# 任务与问题追踪

> 由 Claude Code 自动生成。追踪未完成任务、问题和改进建议。

---

## 待解决问题

<!-- 格式：### [ISSUE-XXX] 标题 (日期) -->

### [ISSUE-001] monte_carlo_finals.py 超过 600 行硬限制 (2026-05-30)
- 文件 `football-server/scripts/monte_carlo_finals.py` 当前 716 行，超出 600 行硬限制
- 需委派 refactor-expert 子智能体进行模块化拆分（模拟引擎 / 策略模型 / 结果输出）

### [ISSUE-003] add-todo.sh 脚本静默失败：返回成功但不写入 todo.md (2026-06-16)
- `bash .claude/scripts/add-todo.sh <type> ...` 两次执行（ISSUE-002 的 issue 记录 + done 记录）均返回 `[OK] ... recorded`，但 grep todo.md 无匹配——脚本静默失败，任务留痕丢失
- 影响：违反 CLAUDE.md 第6节"即时记录原则"的可靠性，依赖该脚本的留痕（含 Stop Hook 兜底）可能静默失效
- 待排查：脚本的写入逻辑（目标文件路径 / 权限 / ID 分配 / 区块定位），修复前改用手动 Edit `.docs/todo.md`

---

## 待办任务

<!-- 格式：- [ ] 任务描述 — @上下文 (日期) -->

- [ ] 比赛详情 AI 分析按钮功能实现 — @match-detail-dialog + ai-controller (2026-05-28)
  - 前端：MatchDetailDialog 增加"AI 分析"按钮 + Skill 选择，复用 SSE 流式管道（P5-06）
  - 回调接线 + 移动端适配 + i18n（P5-07）
- [ ] 补充 G组、H组第1轮（6月15日）实际比赛结果 — @data/2026_FIFA_World_Cup_Group_Stage.md (2026-06-15)
  - G组：比利时 vs 埃及、伊朗 vs 新西兰
  - H组：西班牙 vs 佛得角、沙特阿拉伯 vs 乌拉圭
  - 依据：截至 6/15 权威页面（Wikipedia）尚未录入完整比分，项目 R1 复盘范围仅为 6/11–6/14 共 12 场（见"已完成"区），此 4 场待官方结果确认后回填

---

## 改进建议

<!-- 格式：- 💡 建议 — @上下文 (日期) -->

- 💡 [高] 新增"附加赛/资格赛淬炼"平局加成因子：附加赛晋级队触发额外 draw_boost。依据：2026 R1 B组波黑、卡塔尔两支附加赛队伍均逼平排名更高的对手（加拿大1-1、瑞士1-1），导致两场 HIGH 置信度强队胜翻车。@skills/group_stage_round_strategy.md (2026-06-15)
- 💡 [中] CAF/AFC 球队"五大联赛球员占比高"时上调 TACTICAL_STRETCH 触发概率。依据：E_M2 科特迪瓦 1-0 厄瓜多尔爆冷未被预警。@skills/group_stage_round_strategy.md (2026-06-15)
- 💡 [中] 大球信号对"实力有差距"场次上调进球量级预估。依据：D_M1 美国4-1、F_M2 瑞典5-1、E_M1 德国7-1 均大幅超出预期进球数。@skills/group_stage_round_strategy.md (2026-06-15)
- 💡 [低] system_prompts.py 的 custom_analysis_intro 引导文本将"STEP 0 → STEP 6"措辞补为"STEP 0 → STEP 6（含 v1.1 STEP 3.5）"。依据：v1.1 新增 STEP 3.5 后引导文字未同步；但因该模板动态拼接 skill 全文，STEP 3.5 已自动包含，仅措辞优化，非功能性问题。@football-server/app/services/prompts/system_prompts.py (2026-06-15)

---

## 已完成

<!-- 格式：- [x] 任务描述 — 完成于 YYYY-MM-DD -->

*（暂无已完成项）*

- [x] P5-04 前端 AI 分析 SSE 客户端 + 类型定义 — 完成于 2026-05-28
  - 新增 `football-web/lib/api/match-analysis.ts`（streamMatchAnalysis + getAvailableSkills）
  - 修改 `football-web/lib/api/ai-chat.ts`（导出 parseSSELines、parseSSEPayload、StreamCallbacks）
- [x] P5-03 后端新增 POST /api/ai/match-analysis + GET /api/ai/skills 端点 — 完成于 2026-05-28
- [x] 同步 2026 世界杯 R1 首轮（6/11–6/14 共12场）实际结果至预测报告，胜平负方向命中率 8/12=66.7% — 完成于 2026-06-15
  - 更新 `skills/group_stage_round_strategy-2026_r1_prediction.md`：顶部状态标注、3.1 预测vs实际对照表、新增第六章实际结果复盘（命中率分层 / 命中失败深度评价 / 信号有效性验证 / v1.1 校准建议）
- [x] group_stage_round_strategy 升级至 v1.1：新增「名次价值×体力博弈」分析维度 — 完成于 2026-06-15
  - 新增 STEP 3.5（名次价值 SV × 体力经济学 energy_factor）：将 urgency 由二元出线判断升级为 SEALED 四子态（SEED_MATTERS/SEED_SET/NEUTRAL/TANK），核心动机=已出线是否值得拼取决于该名次淘汰赛对手水平
  - STEP 6 淘汰赛路径分析前置至 R2（R2 概率预估/R3 精确计算）为 STEP 3.5 提供 path_diff；STEP 5.2/5.3 合成联动子态（SEED_MATTERS 抑制爆冷，避免"锁定但认真争名次"被误判为放水）
  - 同步 .docs/business-overview.md + agent-file-map.md 版本描述
- [x] [ISSUE-002] 修复 round_strategy R2/R3 无法获取/推理真实淘汰赛对手 — 完成于 2026-06-16
  - 背景：派生时丢失原模型 `knockout_bracket_snapshot` 入口，STEP 6 仅靠文字引用外部对阵表 + 概率裸估算，path_diff 不可靠污染 STEP 3.5.2 SV → SEALED 子态（TANK/SEED_MATTERS）误判
  - v1.4 改造：①新增内嵌「2026 淘汰赛对阵结构参考」章节（半区速查/R32对阵/第三名约束/第三轮时间线，镜像权威源 `skills/冠亚军分析.md` 2.1-2.5）；②STEP 0.5 新增阶段三·跨组出线快照与 opponent_graph（聚合 data md 12组已完成行）；③STEP 6 重写为消费 opponent_graph 的结构化对手推理（DETERMINED/CANDIDATE_SET/THIRD_POOL 三态 + 正式 confidence 字段 + R3 info_clarity 折损）；④STEP 3.5.2 SV 阈值随 confidence 联动 + SEALED_TANK 触发收紧；⑤STEP 5.3 knockout_path_bias 按 confidence 折损
  - 文件 `skills/group_stage_round_strategy.md`（v1.3→v1.4）
