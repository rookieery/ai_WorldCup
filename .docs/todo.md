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

- [ ] 将 knockout_stage_round_strategy 注册到后端 _SKILL_REGISTRY — @football-server/app/services/prompt_builder.py (2026-06-27)
  - 背景：新增的 `skills/knockout_stage_round_strategy.md`（v1.2）目前仅为方法论文件，尚未接入后端 `_SKILL_REGISTRY`（当前注册 4 个 skill：group_stage_predict / group_stage_round_strategy / knockout_stage_predict / championship_predict）
  - 待办：在 `_SKILL_REGISTRY` 增加该 skill 条目（key + 文件路径 + 描述），同步更新 `.docs/business-overview.md` 第 240-245 行的技能清单（当前仅列 4 个）
  - 验证：前端 MatchDetailDialog 的 Skill 选择器应能拉取到新 skill；与 knockout_stage_predict 的关系类比 group_stage_predict ↔ group_stage_round_strategy（基础模型 ↔ 阶段策略定制版）

- [ ] 比赛详情 AI 分析按钮功能实现 — @match-detail-dialog + ai-controller (2026-05-28)
  - 前端：MatchDetailDialog 增加"AI 分析"按钮 + Skill 选择，复用 SSE 流式管道（P5-06）
  - 回调接线 + 移动端适配 + i18n（P5-07）
- [x] 补充 G组、H组第1轮（6月15日）实际比赛结果 — 完成于 2026-06-22（数据已回填并经 Wikipedia 核实）
  - G组：比利时1-1埃及、伊朗2-2新西兰；H组：西班牙0-0佛得角、沙特1-1乌拉圭
  - @data/2026_FIFA_World_Cup_Group_Stage.md
- [ ] 补充 K/L 组 R2 第二轮预测（6/24 共4场）— @skills/group_stage_round_strategy-2026_r2_prediction.md (2026-06-17)
  - K组：葡萄牙vs乌兹别克斯坦、哥伦比亚vs刚果(金)；L组：英格兰vs加纳、巴拿马vs克罗地亚
  - 依据：K/L 两组 R1（6/18）尚未完赛，R2 预测需基于 R1 实际结果，待 R1 公布后按 v1.4 推理链补充（I/J 组 R2 已于 2026-06-17 完成）
- [ ] 补充 K/L 组 R3 第三轮预测（6/28 共4场）— @skills/group_stage_round_strategy-2026_r3_prediction.md (2026-06-23)
  - K组：哥伦比亚vs葡萄牙、刚果民主共和国vs乌兹别克斯坦；L组：巴拿马vs英格兰、克罗地亚vs加纳
  - 依据：K/L 两组 R2（6/24）尚未完赛（data md 仍为"-"），R3 预测需基于 R1+R2 实际结果，待 R2 公布后按 v1.5 推理链补充（A-J 组 R3 已于 2026-06-23 完成，含 STEP 4 第3名出线池跨组实时门槛 + STEP 6 淘汰赛路径博弈）
- [ ] 同步小组赛数据文件 J/K/L 组第3轮结果 — @data/2026_FIFA_World_Cup_Group_Stage.md (2026-06-27)
  - 进度：A–I 组小组赛全部完赛（D/E/F/H/I 第3轮 + G 第3轮均已回填，见"已完成"区）；仅剩 J/K/L
  - 待办：J组第3轮（约旦vs阿根廷、阿尔及利亚vs奥地利）、K组第3轮（哥伦比亚vs葡萄牙、刚果民主共和国vs乌兹别克斯坦）、L组第3轮（巴拿马vs英格兰、克罗地亚vs加纳）均为 6/28，待开赛后回填
  - 收尾：J/K/L 第3轮回填后，最终复核 1/16 文件（data/2026_FIFA_World_Cup_Round_of_32.md）剩余待定对阵（J/K/L 组排名 + 最佳第3名最终分配）；Group_Stage.md 头部进度说明待同步

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

- [x] 回填 G组第3轮结果（2场）— 完成于 2026-06-27
  - 第3轮：埃及1-1伊朗（Saber 5' / Rezaeian 14'，伊朗补时进球被 VAR 判无效）、新西兰0-3比利时（特罗萨德梅开二度含81'锁定比分）
  - 最终积分：比利时/埃及同5分，比利时净胜球+3反超埃及+2登顶（2026 规则 H2H 先于总净胜球，但比埃 H2H 1-1 全平 → 轮到总净胜球，比利时凭 3-0 大胜反超）；伊朗第3（3分，三连平）、新西兰第4（1分）出局
  - 出线：比利时（第1）、埃及（第2）直接晋级32强；伊朗（3分）进入最佳第3名评选；新西兰出局
  - 验证：ESPN/Al Jazeera/NYT 确认 埃及1-1伊朗；beIN SPORTS 引述"特罗萨德81分钟将比分锁定为3-0"；FIFA 官方积分榜/Yahoo 确认"比利时反超埃及登顶"；GD 反推（比利时需赢3+才能反超埃及+2，3-0 恰满足）；英文维基 Group G 页面尚未录入第3轮（滞后），本数据先于维基更新
  - 关联 1/16 文件：G2 埃及 vs D2 澳大利亚 对阵现可锁定（待复核 data/2026_FIFA_World_Cup_Round_of_32.md）；G1 比利时 vs 最佳第3名 仍待第3名池最终确定
  - @data/2026_FIFA_World_Cup_Group_Stage.md

- [x] 同步小组赛数据文件 D/E/F/H/I 组第3轮结果（10场）— 完成于 2026-06-27
  - 第3轮：D组 土耳其3-2美国（dead rubber，东道主轮换仍败、土耳其24年来世界杯首胜）、巴拉圭0-0澳大利亚；E组 厄瓜多尔2-1德国（爆冷，德国自2022负日本后再遭大赛冷门）、库拉索0-2科特迪瓦；F组 突尼斯1-3荷兰、日本1-1瑞典；H组 乌拉圭0-1西班牙（巴埃纳制胜球）、佛得角0-0沙特；I组 挪威1-4法国、塞内加尔5-0伊拉克
  - 同步补齐赛前积分/排名/热度/爆冷 + D/E/F/H/I 组最终积分与出线；爆冷2场（土耳其胜东道主、厄瓜多尔逆转德国）；E组德国/科特迪瓦同6分凭相互胜负（德国2-1科特迪瓦）定头名（2026 规则 H2H 先于总净胜球）；H组佛得角三连平成1990年来首支"无胜晋级"球队
  - 验证：Wikipedia 各组页面积分榜 GF/GA 反推（如德国 GF10=7+2+1、挪威1-4法国由挪威 GF8/GA7 反推、塞内加尔5-0伊拉克由塞内加尔 GF8/GA6 反推）+ BBC/天空体育战报交叉确认；与 1/16 文件（data/2026_FIFA_World_Cup_Round_of_32.md）D/E/F/H/I 排名交叉核对一致
  - 未完：G/J/K/L 组第3轮未回填（G今日开赛待权威确认、J/K/L 为 6/28），见上方待办
  - @data/2026_FIFA_World_Cup_Group_Stage.md

- [x] 更新 1/16决赛数据文件至 Wikipedia 6/27 最新赛果 — 完成于 2026-06-27
  - `data/2026_FIFA_World_Cup_Round_of_32.md`：依据 Wikipedia knockout stage 页面（6/27 02:02 UTC 快照）+ Group D/E/F 页面复核
  - 已锁定 8 场保持不变（M73/M74/M75/M76/M77/M78/M81/M86），但 M74/M77/M81 的"最佳第3名"由原 Annex C 稳定性推断升级为**实际确认**（3D巴拉圭、3F瑞典、3B波黑随 B/D/F 组完赛确认晋级）
  - **新增候选收窄 5 场**（495 种组合仅 15 种仍可能）：M79 候选 C/E/F/H/I→C/E、M80 E/H/I/J/K→I/J/K、M82 A/E/H/I/J→A/I/J、M85 E/F/G/I/J→E/G/I/J、M87 D/E/I/J/L→E/I/L；M83/M84/M88 仍待 G/J/K/L 组排定
  - 同步数据基准说明（补 Wikipedia 快照来源、H 组第3名出局、已确认 4 席最佳第3名）；时间/场馆经逐场时区换算核对（与 Wikipedia 一致，无改动）
  - 关联：Group_Stage.md 的 D/E/F 第3轮结果回填仍待办（见上方待办），回填后两文件可交叉核对
  - @data/2026_FIFA_World_Cup_Round_of_32.md

- [x] 新增淘汰赛阶段策略 skill（knockout_stage_round_strategy v1.2）+ 2018/2022 双回测 — 完成于 2026-06-27
  - 新增 `skills/knockout_stage_round_strategy.md`：派生自 `knockout_stage_predict` v1.0，对齐 `group_stage_round_strategy` 的"轮次策略定制版"范式。删除小组赛专属步骤（STEP 3.5 名次价值博弈 / STEP 4 第3名出线 / STEP 6 路径选择），聚焦"硬实力(FIFA排名) + 当年小组赛表现(GSPI)"双支柱。6 阶段猎手模式：R32碾压/R16特质/QF黑马(特质×1.3)/SF回归/3RD经验/FINAL心理
  - 新增 `skills/knockout_stage_round_strategy-2022_backtest.md`（16场）：90min方向 14/16(87.5%)、晋级 15/16(93.75%)、爆冷预警 3/3、点球大战预测 5/5 全中。摩洛哥/克罗地亚防守型黑马标杆
  - 新增 `skills/knockout_stage_round_strategy-2018_backtest.md`（16场）：90min方向 10/16(62.5%)、晋级 12/16(75%)。连续加时体能考在决赛的决定性价值（克罗地亚3场加时→法国方向胜出）、双支柱势头覆盖（法国胜阿根廷/乌拉圭胜葡萄牙）
  - v1.2 反哺校准：①连续加时体能正式化为 STEP 1.5 路径消耗修正；②DEFENSIVE_DARK_HORSE 门槛 rank>15 放宽为 underdog+防守特质（修复2022克罗地亚rank12漏判）；③DUAL_ATTACK counter≥5 额外+0.04（跨届：2018巴比/2022英法）；④东道主累积+0.05/场；⑤rank_diff>40+对手东道主/点球专家→favored_win×0.85；⑥MOMENTUM_UNDERDOG +0.06→+0.08；⑦draw_base R16/SF 微调；⑧SF def_res≥4 +0.04
  - 同步 `skills/README.md`：Skills 表新增行、数据流图新增淘汰赛策略分支、推理链架构更新为8步、数据源补 2018
  - @skills/knockout_stage_round_strategy.md @skills/knockout_stage_round_strategy-2018_backtest.md @skills/knockout_stage_round_strategy-2022_backtest.md
- [x] 新增 2026 世界杯 1/16决赛（32强淘汰赛）赛程数据文件 — 完成于 2026-06-27
  - 新增 `data/2026_FIFA_World_Cup_Round_of_32.md`：16 场（Match 73–88）完整赛程，含 FIFA 官方对阵模板、北京时间（UTC+8）开球、14 座场馆；附 1/8决赛（Match 89–96）对阵前瞻
  - 已锁定对阵 8 场（M73 南非vs加拿大 / M74 德国vs巴拉圭 / M75 荷兰vs摩洛哥 / M76 巴西vs日本 / M77 法国vs瑞典 / M78 科特迪瓦vs挪威 / M81 美国vs波黑 / M86 阿根廷vs佛得角）；其中 M74/M77/M81 涉及"最佳第3名"，经 Annex C 矩阵验证（所有仍可能的小组赛结果组合下对手不变）故可锁定
  - 未锁定 8 场以占位符表示（最佳第3名分配 + G/K/L 组排名待定）；同步 .docs/README.md 数据索引 + agent-file-map.md 目录树
  - 数据来源：Wikipedia 2026 knockout stage（6/27 编辑）+ FIFA 赛事规程 Annex C 矩阵
- [x] 更新 2026 小组赛最新比赛结果（A/B/C 组第3轮 6 场 + K/L 组第2轮 4 场，共 10 场）— 完成于 2026-06-25
  - 第3轮：捷克0-3墨西哥、南非1-0韩国、瑞士2-1加拿大、波黑3-1卡塔尔、苏格兰0-3巴西、摩洛哥4-2海地
  - 第2轮补漏（K/L 组原文件为"-"）：葡萄牙5-0乌兹别克斯坦（C罗成首位6届世界杯进球球员）、哥伦比亚1-0刚果(金)、英格兰0-0加纳、巴拿马0-1克罗地亚
  - 同步补齐赛前积分/排名/热度/爆冷 + A/B/C 组最终积分与出线；爆冷 2 场（南非1-0韩国末位逆袭、英格兰0-0加纳被弱旅逼平）
  - 出线：墨西哥/南非、瑞士/加拿大、巴西/摩洛哥直接晋级32强；韩国、波黑、苏格兰进入8支最佳第3名评选
  - 验证：Wikipedia 各组页面（Group A/B/C/K/L）GF/GA 反推 + BBC/ESPN/Guardian 交叉确认；D-L 组第3轮（北京 6/26-28）未开赛保持"-"
  - @data/2026_FIFA_World_Cup_Group_Stage.md
- [x] group_stage_round_strategy 升级至 v1.5：重写 STEP 4 第3名出线为跨组实时排名对比 — 完成于 2026-06-23
  - 背景：STEP 4 此前用固定门槛表（4分>95%/3分~50%/2分20-30%/1分<5%），无视本届实际第3名竞争态势——第3名出线是12组第3名的相对竞争（取前8），门槛表在低分扎堆格局下系统性失准。阶段三早已声明把 candidates_3nd 回灌 STEP 4，但方法论此前未兑现（v1.4 改造 STEP 6 时遗漏的同源问题）
  - v1.5 改造：①STEP 4 重写为消费 group_standings_snapshot 的跨组实时第3名排名对比；②新增实时出线门槛 advancement_threshold_points（门槛表给不出的"本届几分能出线"）；③落第3情景枚举（9组合确定性推演本队是否落第3）；④第3名池排名对比替代查表；⑤confidence 分级联动 info_clarity（R2/迷雾组输出概率区间，R3透明组接近精确）；⑥impact_on_match 按 confidence 折损（HIGH=1.0/MEDIUM=0.6/LOW=0.3）
  - 联动同步：meta 版本号、STEP 5.3 step4 消费注释、阶段三回灌措辞、输出 schema、权重表 R3、使用说明、末尾版本号；.docs/agent-file-map.md + business-overview.md 版本描述
  - 文件 `skills/group_stage_round_strategy.md`（v1.4→v1.5）
- [x] 更新 2026 小组赛 I/J组第2轮比赛结果（4场）— 完成于 2026-06-23
  - 第2轮：法国3-0伊拉克、挪威3-2塞内加尔、阿根廷2-0奥地利、约旦1-2阿尔及利亚
  - 同步补齐赛前积分/排名/热度/爆冷；4场均为强队/领先方取胜，无爆冷
  - 验证：ESPN/FIFA Match Centre 交叉确认；K/L组第2轮（北京6/24）及全部第3轮未开赛保持"-"
  - @data/2026_FIFA_World_Cup_Group_Stage.md
- [x] 更新 2026 小组赛最新比赛结果（A-H组第2轮16场 + K/L组第1轮4场，共20场）— 完成于 2026-06-22
  - 第2轮：墨西哥1-0韩国、捷克1-1南非、加拿大6-0卡塔尔、瑞士4-1波黑、巴西3-0海地、苏格兰0-1摩洛哥、美国2-0澳大利亚、土耳其0-1巴拉圭、德国2-1科特迪瓦、厄瓜多尔0-0库拉索、荷兰5-1瑞典、突尼斯0-4日本、比利时0-0伊朗、新西兰1-3埃及、西班牙4-0沙特、乌拉圭2-2佛得角
  - 第1轮补漏（K/L组原文件未填）：葡萄牙1-1刚果(金)、乌兹别克斯坦1-3哥伦比亚、英格兰4-2克罗地亚、加纳1-0巴拿马
  - 同步补齐赛前积分/排名/热度/爆冷；爆冷6场（土耳其0-1巴拉圭、厄瓜多尔0-0库拉索、乌拉圭2-2佛得角、葡萄牙1-1刚果(金)、加纳1-0巴拿马、及弱队逼平强队类）
  - 验证：Wikipedia 各组积分榜 GF/GA 反推 + ESPN/Reuters/FOX 交叉确认；I/J/K/L 第2轮（北京6/23-24）未开赛保持"-"
  - @data/2026_FIFA_World_Cup_Group_Stage.md

- [x] 补充 I/J 组 R2 第二轮预测（6/23 共4场）— 完成于 2026-06-17
  - I_M1 法国vs伊拉克（法国胜 HIGH）、I_M2 挪威vs塞内加尔（塞内加尔胜 MEDIUM，最开放）、J_M1 阿根廷vs奥地利（阿根廷胜 MEDIUM，卫冕冠军×0.80）、J_M2 约旦vs阿尔及利亚（阿尔及利亚胜 MEDIUM，惨败修正）
  - 基于 data md 的 I/J R1 实际结果（法国3-1塞内加尔、挪威4-1伊拉克、阿根廷3-0阿尔及利亚、奥地利3-1约旦），按 v1.4 推理链逐场分析；联动更新报告范围 A–H(16场)→A–J(20场)、概览统计、爆冷预警、头名之争汇总、排名虚假度表、卫冕冠军动态系数（R1 正常胜→0.80 已确认）
  - @skills/group_stage_round_strategy-2026_r2_prediction.md

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
- [x] 生成 2026 世界杯小组赛 R2 第二轮预测报告（A–H组16场）— 完成于 2026-06-16
  - 新增 `skills/group_stage_round_strategy-2026_r2_prediction.md`：基于 v1.4 推理链（STEP 0.5 FIFA排名+历史轮次+出线快照 / STEP 1-6 / 5.5）
  - 仅对 R1 已完赛小组（A–H，data md 已录入 G/H 6/15 结果）做详细预测；I/J/K/L 组（R1 6/16–6/17 未完赛）仅记录标题待补充
  - 16场方向分布：强队胜11 / 平3 / 爆冷2；HIGH置信度7场；3场头名之争（A_M3/D_M3/E_M3）标 HIGH_STABILITY 候选；排名虚假度修正命中4场（D_M4/E_M4/H_M3/H_M4）；B/G/H 三组四队同分迷雾组为平局/爆冷高发区
