# Skill: knockout_stage_round_strategy — 淘汰赛阶段策略预测

## 元信息

- **版本**: 1.2（2018+2022淘汰赛双重复测校准版）
- **适用赛制**: 2026年世界杯淘汰赛（R32 1/16 → R16 1/8 → QF 1/4 → SF 半决赛 → 3RD 三四名 → FINAL 决赛）；通过赛制适配指南可回测2018/2022
- **分析粒度**: 阶段差异化策略预测——R32硬实力碾压猎手、R16特质猎手、QF黑马猎手、SF实力回归猎手、3RD经验猎手、FINAL心理猎手
- **核心定位**: 阶段策略引导——每个淘汰赛阶段有独立的策略方向，输出"90分钟赛果 + 晋级预测（含加时/点球）"双层结果
- **派生来源**: knockout_stage_predict v1.0 — 继承特质匹配与加时/点球框架，新增"硬实力×当年小组赛表现"双支柱基线与阶段差异化合成
- **设计取舍（相对 group_stage_round_strategy）**:
  - **删除 STEP 3.5 名次价值×体力博弈**——淘汰赛不存在"选名次/控分"，本场即生死战，名次博弈逻辑不适用
  - **删除 STEP 4 第3名出线概率**——小组赛专属概念；2026的"小组第3名出线队"在淘汰赛中被折叠为 STEP 1 的"第3名实力折损"修正，而非独立出线博弈步骤
  - **删除 STEP 6 淘汰赛路径博弈**——该步骤解决的是"小组赛末轮是否控分选半区"；进入淘汰赛后对阵结构已由抽签+小组排名完全锁定，路径博弈对象消失
  - **强化"硬实力 + 当年小组赛表现"双支柱**——FIFA排名是静态纸面实力，当年小组赛3场实测表现是最实时、最可信的实力代理（碾压 2018俄罗斯#70、2022比利时#2 的排名失真问题）
- **v1.1 新增**：双支柱硬实力基线（STEP 1）+ 阶段差异化爆冷/平局系数（STEP 2）+ 心理韧性分析前置（STEP 3）+ 加时/点球分支纳入晋级合成（STEP 5/6）。校准来源：2018+2022共32场淘汰赛（平局率31.25%、点球率28.1%、QF黑马巅峰、防守型黑马规则）
- **v1.2 反哺（2018+2022双回测校准）**：①**连续加时体能考正式化**为 STEP 1 路径消耗修正 `consecutive_et_penalty`（2018克罗地亚决赛连续3场加时崩盘、2022克罗地亚/摩洛哥SF脆败的跨届核心规律）；②**DEFENSIVE_DARK_HORSE 触发门槛放宽**：`rank>15` 收紧为"underdog(排名低于对手)+defensive_resilience≥4+clean_sheets≥1+场均失球<1.0"（修复2022克罗地亚rank12淘汰巴西的漏判）；③**DUAL_ATTACK 反击加权**：`counter_attack_efficiency≥5` 额外 favored+0.04（2018巴西vs比利时、2022英格兰vs法国跨届一致失败）；④**东道主累积效应**：连续爆冷时 HOST_FORTRESS 递增+0.05/场（2018俄罗斯连爆3场）；⑤**rank_diff>40强队胜率下调**：对手为东道主/点球专家时 favored_win×0.85；⑥**MOMENTUM_UNDERDOG 权重提升** +0.06→+0.08（含对强队大胜再+0.04）；⑦**draw_base 微调**（R16+0.03/SF+0.04）+ 顶级零封铁桶(clean_sheets≥2)的 L 权重提升；⑧**SF 防守加权**：defensive_resilience≥4 额外+0.04。回测结果：2018 90min方向62.5%/晋级75%、2022 90min方向87.5%/晋级93.75%（详见对应回测文件）
- **使用方式**: 自包含 prompt，可直接交给具备 web search 能力的大模型独立执行

---

## 爆冷定义

淘汰赛的"爆冷"语义与小组赛不同：小组赛爆冷=弱队胜/平强队；**淘汰赛爆冷=排名明显较低（rank_diff≥10）的球队在90分钟内不败（胜或平）或最终晋级**。淘汰赛允许90分钟平局，因此爆冷有两个层级：

- **全爆冷 (Full Upset)**：弱队在90分钟内胜（favored 负）→ 映射为弱队晋级
- **拖入决胜爆冷 (Decider Upset)**：弱队90分钟逼平强队 → 进入加时/点球，并最终晋级（如 2018俄罗斯点球淘汰西班牙、2022摩洛哥点球淘汰西班牙、2022克罗地亚点球淘汰巴西）

> **关键规律**：淘汰赛爆冷高度集中在**防守型黑马**身上（2022摩洛哥、两届克罗地亚、2018俄罗斯东道主）。这类球队共同特征——世界排名不高但防守极韧、点球大战能力突出，把比赛拖入低消耗的决胜局后以韧性取胜。排名差在淘汰赛中解释力显著低于小组赛（详见 STEP 2）。

---

## 历史数据基线（2018+2022，共32场淘汰赛）

| 指标 | 2018(16场) | 2022(16场) | 合计(32场) | 策略含义 |
|------|-----------|-----------|-----------|---------|
| 90分钟平局率 | 31.25% (5/16) | 31.25% (5/16) | **31.25%** (10/32) | 远高于小组赛(~25%)，平局预测权重必须上调 |
| 加时赛率 | 31.25% (5/16) | 31.25% (5/16) | 31.25% | 约三成比赛进入加时 |
| 点球大战率 | 25.0% (4/16) | 31.25% (5/16) | **28.1%** | 加时几乎都拖入点球（2018/2022加时内解决率=0%） |
| 爆冷率（数据标记） | 18.75% (3/16) | 18.75% (3/16) | 18.75% | QF是爆冷巅峰轮 |
| 高排名方90分钟胜率 | — | — | ~50% | 排名优势在90分钟被大幅稀释 |

**按阶段爆冷/平局分布（两届合计）**：

| 阶段 | 场次 | 平局率 | 爆冷率 | 策略模式 |
|------|------|--------|--------|---------|
| R16(1/8) | 16 | 25% (4/16) | 12.5% | 实力为主、特质初现 |
| QF(1/4) | 8 | 37.5% (3/8) | 25% | **黑马巅峰轮**——特质权重×1.3 |
| SF(半决赛) | 4 | 25% (1/4) | 25% | 黑马力竭、回归实力 |
| FINAL(决赛) | 2 | 50% (1/2) | 0% | 极端压力、保守高平局 |
| 3RD(三四名) | 2 | 0% | 0% | 低压力开放局 |

---

## 阶段策略方向总览

| 阶段 | 策略模式 | 核心关注 | 推荐输出优先级 |
|------|---------|---------|-------------|
| R32 | 硬实力碾压猎手 | 硬实力碾压、小组第3名折损、强弱悬殊 | 强队胜比分 > 大球比分 > 爆冷 |
| R16 | 特质猎手 | 特质匹配主导、防守型黑马启动、加时/点球初现 | 特质偏向比分 > 平局 > 爆冷 |
| QF | 黑马猎手 | 黑马巅峰轮、特质权重×1.3、防守反击爆冷 | 按特质剧本分支 |
| SF | 实力回归猎手 | 硬实力回归、黑马力竭、阵容深度 | 强队稳定晋级 > 加时 |
| 3RD | 经验猎手 | 低压力、大赛经验、阵容深度、开放大球 | 大球比分 > 经验方胜 |
| FINAL | 心理猎手 | 极端压力、逆转基因、大赛经验、保守高平局 | 平局/小比分 > 加时点球 |

---

## 输入规范 (Input Schema)

```json
{
  "match": {
    "match_id": "string — 如 'R16_03'",
    "stage": "string — 'R32' | 'R16' | 'QF' | 'SF' | '3RD' | 'FINAL'",
    "home_team": "string",
    "away_team": "string"
  },
  "teams": {
    "<team_name>": {
      "fifa_ranking": "integer — 赛前FIFA世界排名（STEP 0.5阶段一从 data md 自动回灌）",
      "world_cup_experience": "integer — 历史参赛次数（必填）",
      "confederation": "string — UEFA/CONMEBOL/AFC/CAF/CONCACAF/OFC（必填）",
      "group_stage_output": {
        "group": "string — 来源组别",
        "group_position": "integer — 1 | 2 | 3（2026有3，2018/2022仅1/2）",
        "group_points": "integer — 小组赛3场总积分(0-9)",
        "group_goals_for": "integer",
        "group_goals_against": "integer",
        "goal_difference": "integer",
        "group_form": "string — 如 'W-D-W'（按R1→R3顺序）",
        "clean_sheets": "integer — 小组赛零封场次(0-3)",
        "is_host": "boolean — 是否东道主"
      },
      "team_traits": {
        "defensive_resilience": "integer 1-5 — 防守韧性",
        "counter_attack_efficiency": "integer 1-5 — 反击效率",
        "set_piece_threat": "integer 1-5 — 定位球威胁",
        "penalty_track_record": "integer 1-5 — 点球大战历史表现",
        "comeback_gene": "integer 1-5 — 逆转能力/精神属性",
        "tournament_experience": "integer 1-5 — 大赛经验深度",
        "squad_depth": "integer 1-5 — 阵容深度"
      }
    }
  },
  "tournament_context": {
    "completed_knockout_matches": "object — 本届已完赛淘汰赛结果（SF/3RD/FINAL前瞻时用于评估对手体能/路径消耗）"
  },
  "tournament_config": {
    "host_count": "integer — 2026=3(美加墨), 2018=1, 2022=1",
    "has_third_place_qualified": "boolean — 2026=true(8个小组第3名), 2018/2022=false",
    "champion_match_count": "integer — 夺冠所需场次：2026=8(3小组+5淘汰), 2018/2022=7"
  }
}
```

---

## 推理步骤链 (Reasoning Chain)

执行顺序：
  全阶段：STEP 0 → 0.5(阶段一: FIFA排名 + 阶段二: 小组赛表现) → 1(硬实力双支柱) → 2(爆冷模式+阶段系数) → 3(动机与心理) → 4(特质匹配) → 5(加时/点球) → 6(阶段合成) → 6.5(比分推荐)

注1：STEP 0.5 阶段一（FIFA 排名）与阶段二（小组赛表现）**全阶段执行**——STEP 1 的双支柱基线依赖两者，R32 也不能跳过。
注2：STEP 4（特质匹配）是淘汰赛的核心差异化步骤，权重在 QF 阶段×1.3 放大。
注3：STEP 5（加时/点球）当 STEP 2/4 判定平局概率≥0.28 或特质剧本为 ATTACK_VS_FORTRESS 时触发，否则跳过。

---

### STEP 0: 实时数据获取 (Realtime Data Acquisition)

> 继承通用能力。淘汰赛必搜清单侧重"赛前48小时状态 + 历史交锋 + 点球门将"。

**必搜清单**：
- P0: 双方小组赛后体能/伤病恢复、核心球员出战状态、主帅轮换意向
- P1: 双方历史交锋（尤其近5年大赛）、点球大战历史胜率与门将
- P2: 赔率（含"是否加时/点球"专项赔率）、本届已完赛淘汰赛对手消耗

**数据整理**：`realtime_data = { {{team}}: { recent_form, key_injuries: [{impact}], coach_intent, penalty_history }, h2h, market_odds }`

---

### STEP 0.5: 数据源加载 (Data Source Loading)

> 双阶段全执行。阶段一加载 FIFA 排名（硬实力静态档位），阶段二加载**当年小组赛表现**（最实时实力代理——本策略相对 knockout_stage_predict 的核心增强）。

---

#### 阶段一 · FIFA 排名加载 (FIFA Ranking Loading) — 全阶段

**读取目标**：本场对阵双方的 FIFA 世界排名，回灌 `teams.{home,away}.fifa_ranking`。

**解析规则**：

| 场景 | 数据文件 | 解析逻辑 |
|------|---------|---------|
| 2026 前瞻 | `data/2026_FIFA_World_Cup_Round_of_32.md`（或 Group_Stage.md 标注说明） | 「FIFA排名(主/客)」列或汇总表 |
| 2018/2022 回测 | `data/{year}_FIFA_World_Cup_Results.md` | 淘汰赛表格「FIFA排名(主/客)」列 + 标注说明汇总表 |

**降级链**（值缺失逐级回退，标注 `fifa_ranking_source`）：小组表格值 → 汇总表 → input 占位值 → missing（阻断 STEP 1）。

**语义铁律**：FIFA 排名是**开赛前最新一期静态世界排名**（全赛事恒定），与小组赛"组内排名"（积分榜动态排名）语义截然不同——STEP 1 的 rank_diff 只取 FIFA 排名。

---

#### 阶段二 · 小组赛表现加载 (Group Stage Performance Loading) — 全阶段

> **核心增强**。FIFA 排名是开赛前快照，无法反映"开赛后球队真实状态"。当年小组赛3场实测表现（积分/净胜球/势头/防守）是最可信的实时实力代理，专门修正 FIFA 排名失真——2018俄罗斯#70 实则5-0沙特碾压、2022比利时#2 实则老化勉强出线，两类失真都由小组赛表现暴露。

**读取目标**：本场双方的小组赛汇总数据，回灌 `teams.{home,away}.group_stage_output`。

**解析字段**（从 data md 各组"最终积分"行 + 逐场比分聚合）：

| 字段 | 解析逻辑 | 喂入目标 |
|------|---------|---------|
| group_position | 组内最终排名(1/2/3) | STEP 1 第3名折损 / STEP 2 黑马信号 |
| group_points | 3场积分(0-9) | STEP 1 实力档修正 |
| goal_difference | 进球-失球 | STEP 1 攻防效率 |
| group_form | R1→R3结果序列(如W-D-W) | STEP 1 势头(momentum) |
| clean_sheets | 零封场次(0-3) | STEP 2 防守型黑马信号 |
| group_goals_against | 失球总数 | STEP 2 防守韧性 |

**输出**：

```json
{
  "step": 0.5,
  "fifa_ranking": { "home": "int", "away": "int", "source": "..." },
  "group_stage": {
    "home": { "position": "int", "points": "int", "gd": "int", "form": "string", "clean_sheets": "int", "goals_against": "int", "is_host": "bool" },
    "away": { "同上" }
  }
}
```

---

### STEP 1: 硬实力双支柱基线评估 (Dual-Pillar Hard Strength Baseline) ⭐核心

> 本策略的根基。FIFA 排名（支柱A·纸面实力）+ 当年小组赛表现（支柱B·实测状态）合成"真实硬实力"，再用阶段系数修正。淘汰赛是单场定胜负的低容错环境，硬实力权重显著高于小组赛。

#### 1.1 支柱A · 纸面实力基线表（基于 rank_diff）

淘汰赛参数（相对小组赛：平局更高、强队统治力更低）：

| 排名差区间 | favored_win | draw | upset |
|-----------|-------------|------|-------|
| 0-8 | 0.36 | 0.32 | 0.32 |
| 9-20 | 0.44 | 0.30 | 0.26 |
| 21-35 | 0.52 | 0.27 | 0.21 |
| 36-50 | 0.60 | 0.23 | 0.17 |
| >50 | 0.66 | 0.20 | 0.14 |

> **v1.2 强队胜率下调**（2018校准）：当 `rank_diff > 40` **且** 弱队满足"东道主(is_host) 或 PENALTY_SPECIALIST 或 DEFENSIVE_DARK_HORSE"之一时，favored_win `× 0.85`。修复 2018西班牙(10)vs俄罗斯(70) rank_diff=60 时 W=0.66 过高、被拖入点球却预测胜的问题。强队面对铁桶+点球门将在90分钟内胜率应下调。

#### 1.2 支柱B · 小组赛表现修正（实测状态校准纸面实力）

对主客双方分别计算"小组赛势头指数 (GSPI)"，再修正 STEP 1.1 的基线概率：

```
// 势头 (momentum)：3场结果序列
wins = count('W' in form)
PERFECT(3胜):   momentum_boost = +0.08
STRONG(2胜1平): momentum_boost = +0.06
GOOD(2胜1负):   momentum_boost = +0.03
STALE(1胜2平):  momentum_boost = -0.02
MIXED(1胜1平1负): momentum_boost = 0.00
WEAK(多平多负): momentum_boost = -0.05
TERRIBLE(≥2负): momentum_boost = -0.08

// 攻防效率 (efficiency)
gd_per_match = goal_difference / 3
DOMINANT(≥+2.0):  eff_boost = +0.06
POSITIVE(≥+0.5):  eff_boost = +0.03
NEUTRAL(≥0):      eff_boost = 0.00
NEGATIVE(<0):     eff_boost = -0.04

GSPI = momentum_boost + eff_boost   // 范围约 [-0.14, +0.14]
```

**纸面-实测冲突修正（关键）**——当 GSPI 与 rank_diff 方向冲突时，**实测状态覆盖纸面实力**（回测校准：2018俄罗斯#70小组+8净胜球→纸面严重低估；2022比利时#2小组仅3分勉强出线→纸面严重高估）：

```
signal_diff = GSPI_home - GSPI_away   // 正值=主队实测更强

IF |signal_diff| >= 0.10 AND signal_diff 与 rank_diff 方向相反:
  // 实测与纸面冲突且实测信号强 → 实测覆盖
  base_home_win += signal_diff * 0.8   // 高权重，实测状态压倒排名
ELSE:
  base_home_win += signal_diff * 0.5   // 默认权重
base_away_win -= signal_diff * 0.5
```

#### 1.3 阶段修正因子 stage_correction

```
R32(硬实力碾压):
  stage_correction = 1.05   // 排名差解释力最强，强弱悬殊多
  特殊: IF 一方 group_position==3 → 该方 favored_win *0.80 (第3名折损，仅2026)
        IF is_host → favored_win += 0.06 (东道主效应，2026三国)

R16(特质初现):
  stage_correction = 1.00   // 基准

QF(黑马巅峰):
  stage_correction = 0.85   // 排名差解释力下降，特质与黑马接管
  特殊: trait_weight_multiplier = 1.3 (特质分析权重×1.3)

SF(实力回归):
  stage_correction = 1.10   // 黑马力竭，回归纸面实力
  特殊: IF 一方已连续打加时/点球(squad_depth<3) → 该方 favored_win -=0.05 (体能透支)
        v1.2: IF 一方 defensive_resilience>=4 → 该方 favored_win +=0.04 (SF是防守决定胜负阶段)

3RD(低压力):
  stage_correction = 0.90   // 排名差失效，心态主导
  特殊: 大球倾向 xG_total *= 1.15 (双方放开打)

FINAL(极端压力):
  stage_correction = 0.95   // 略保守
  特殊: draw_base += 0.05 (决赛高平局)；IF comeback_gene>=4 → 该方 +0.05
```

#### 1.4 卫冕冠军/衰退检测（可选修正）

继承 group_stage 的"卫冕冠军魔咒"与冠亚军分析的"黄金一代衰退"——若一方为卫冕冠军且小组赛表现疲软（GSPI<0），或核心阵容老化信号≥2，则 `favored_win *= 0.80`。淘汰赛阶段此修正力度小于小组赛（已出线的卫冕冠军至少说明硬实力在线）。

#### 1.5 路径消耗修正（连续加时体能考）⭐v1.2 正式化

> **跨届核心规律**（2018克罗地亚决赛连续3场加时崩盘4-2负、2022克罗地亚/摩洛哥SF脆败）。淘汰赛多轮次消耗下，连续加时/点球是后期轮次（SF/Final）的决定性负向因子。本步骤在 R16 之后（QF/SF/Final）对存在连续加时消耗的一方施加体能惩罚。

```
consecutive_et_count = 该队本届淘汰赛已参与的加时赛/点球大战次数（R16之前累计）
// 仅 QF/SF/3RD/FINAL 执行（R16/R32 首场无前序消耗）

consecutive_et_penalty = consecutive_et_count * (-0.06)
// 阶段放大系数：
//   QF:  ×1.0
//   SF:  ×1.0
//   FINAL: ×1.5  (决赛体能崩盘最致命，2018克罗地亚3场加时→决赛-0.18)

IF consecutive_et_count >= 1:
  该队 favored_win += consecutive_et_penalty * stage_et_amplifier
  // squad_depth 不足则进一步放大
  IF squad_depth < 3: penalty *= 1.3
  // 高 MTI(comeback_gene/penalty) 可部分抵消体能惩罚（2018克罗地亚SF仍靠MTI逆转）
  IF MTI >= 4.3: penalty *= 0.7

胜率夹值 [0.05, 0.95]
```

**校准来源**：
- 2018 KO-16 决赛：克罗地亚连续3场加时 → penalty = 3×(-0.06)×1.5 = **-0.27**（squad_depth3不放大，MTI4.3抵消至-0.19），翻转势头覆盖使法国方向胜出（4-2实际）
- 2022 KO-13/14 SF：克罗地亚(2轮点球)、摩洛哥(点球+伤停) → penalty = 2×(-0.06) = -0.12，两队在SF脆败
- 高 MTI 抵消：2018克罗地亚SF(连续2场加时)仍靠 comeback_gene5 逆转英格兰，故 MTI≥4.3 时 penalty×0.7

**输出**：`{ step: 1, rank_diff, gspi_home, gspi_away, signal_diff, signal_conflict: bool, base_probabilities: { favored_win, draw, upset }, stage_correction, stage_special_modifiers, consecutive_et_penalty_home, consecutive_et_penalty_away (v1.2) }`

---

### STEP 2: 爆冷模式识别 + 阶段系数 (Upset Pattern with Stage Multiplier)

> 淘汰赛爆冷高度模式化——集中在防守型黑马、势头型黑马、东道主三类。rank_diff 在此的解释力进一步下降。

**2.1 爆冷模式匹配**：

| 模式标识 | 触发特征 | base_upset_boost | 决胜偏好 |
|---------|---------|-----------------|---------|
| DEFENSIVE_DARK_HORSE | **弱队(排名低于对手, v1.2 放宽不卡绝对rank>15)** AND defensive_resilience≥4 AND clean_sheets≥1 AND 小组赛场均失球<1.0 | **+0.12** | 拖入点球 |
| PENALTY_SPECIALIST | 弱队 AND penalty_track_record≥4 AND tournament_experience≥3 | +0.08 | 点球决胜 |
| MOMENTUM_UNDERDOG | 弱队 AND group_form含2胜(势头GOOD+) AND GSPI>0 | **+0.08 (v1.2 从0.06提升)**；若势头含对种子队大胜(净胜≥2)再 +0.04 | 90分钟或加时 |
| HOST_FORTRESS | 弱队 AND is_host (2018俄罗斯) | **+0.10 + 累积+0.05/连续爆冷场次 (v1.2)** | 加时/点球 |
| DESPERATE_GRINDER | 弱队 无上述特质，纯靠拼劲 | +0.02 | 难爆冷 |

> **v1.2 关键放宽（2022回测反哺）**：DEFENSIVE_DARK_HORSE 原 `rank>15` 绝对门槛会漏判 rank10-15 的防守强队——2022克罗地亚(rank12)淘汰巴西(rank1)按">15"漏判。改为**"排名低于对手(underdog) + defensive_resilience≥4 + clean_sheets≥1 + 场均失球<1.0"**，捕获所有低排名防守铁桶。摩洛哥(rank22)、克罗地亚(rank12)双双纳入。

> **v1.2 东道主累积效应（2018回测反哺）**：东道主连续爆冷时 HOST_FORTRESS 递增——2018俄罗斯连爆西班牙/克罗地亚，每淘汰一支种子队下一场 +0.05。反映东道主信心累积 + 对手重视度不足。

**回测校准（2022+2018）**：
- 2022摩洛哥(22)淘汰西班牙(7)/葡萄牙(9)：DEFENSIVE_DARK_HORSE + PENALTY_SPECIALIST 双触发，+0.20
- 2022克罗地亚(12)淘汰巴西(1)：DEFENSIVE_DARK_HORSE(v1.2放宽后捕获) + PENALTY_SPECIALIST，+0.20
- 2018俄罗斯(70)淘汰西班牙(10)→逼平克罗地亚(20)：HOST_FORTRESS(+0.10→+0.15累积) + PENALTY_SPECIALIST，+0.18~0.23
- 2018瑞典(24)淘汰瑞士(6)：MOMENTUM_UNDERDOG(v1.2 +0.08，含3-0墨西哥大胜+0.04 = +0.12)，跨届验证后权重提升

**2.2 阶段爆冷系数 stage_upset_multiplier**（2018+2022校准）：

```
R32: 0.9   // 硬实力碾压轮，mismatch多，但3rd名折损已压制弱队；爆冷稀少
R16: 1.0   // 基准，特质初现
QF:  1.4   // 黑马巅峰轮——两届合计QF爆冷率25%、平局率37.5%，最高
SF:  0.7   // 黑马力竭（2022摩洛哥SF 0-2负法国），回归实力
3RD: 1.1   // 低压力开放局，偶有意外
F:   0.8   // 决赛压力下硬实力+经验主导，但平局高
```

**最终 upset_boost** = `base_upset_boost × stage_upset_multiplier + 实时修正`

**实时修正**：对方核心球员 HIGH impact 缺阵 → +0.04；弱队近5场胜率≥60% → +0.03；强队主帅确认大幅轮换 → +0.04。

**输出**：`{ step: 2, underdog_pattern, base_upset_boost, stage_upset_multiplier, final_upset_boost, pattern_confidence }`

---

### STEP 3: 阶段差异化动机与心理分析 (Stage-Differentiated Motivation & Psychology)

> 淘汰赛动机高度同质化——双方都是"不赢就回家"的生死战，urgency 基线恒为 1.0。因此本步骤重心从"动机差异"（小组赛核心）转向"**心理韧性差异**"（淘汰赛核心）：大赛经验、逆转基因、点球心理。

**3.1 心理韧性指数 (Mental Toughness Index, MTI)**

```
MTI = tournament_experience * 0.35 + comeback_gene * 0.35 + penalty_track_record * 0.30
// 范围 1.0-5.0

MTI_diff = MTI_home - MTI_away
mental_adjust = MTI_diff * 0.04   // 每差1档约±0.04
```

**3.2 阶段差异化触发**

| 阶段 | 心理修正重点 | 触发逻辑 |
|------|------------|---------|
| R32 | 经验优势弱（强弱悬殊） | mental_adjust × 0.5 |
| R16 | 经验开始显现 | mental_adjust × 1.0 |
| QF | 黑马韧性巅峰 | mental_adjust × 1.3；DEFENSIVE_DARK_HORSE 方额外 comeback_gene 修正 |
| SF | 体能+经验双考 | squad_depth<3 方 favored_win -= 0.05（连续加时透支） |
| 3RD | 经验+深度主导 | tournament_experience≥4 且对方<3 → +0.08；squad_depth≥4 且对方<3 → +0.06 |
| FINAL | 极端压力，逆转基因+经验决定 | comeback_gene≥4 → +0.05；tournament_experience≥4 且对方≤2 → +0.10 |

**3.3 概率修正公式**

```
W_base = step1输出（经 stage_correction + 小组赛表现修正）
D_base = step1输出
L_base = step1输出

// 心理韧性修正（双向）
W_base += mental_adjust (若 home 为 favored 且 MTI 更高)
L_base += -mental_adjust (相应)

// 爆冷修正（弱队方向）
upset_net = step2.final_upset_boost * (1 - abs(MTI_diff) * 0.1)
L_base += upset_net (若弱队 MTI 不逊) OR D_base += upset_net * 0.5 (拖入决胜)

// 边界保护 + 归一化（所有概率 >= 5%）
```

**输出**：`{ step: 3, mti_home, mti_away, mental_adjust, stage_trigger, adjustment: { W_adjusted, D_adjusted, L_adjusted } }`

---

### STEP 4: 特质匹配分析 (Trait Matchup Analysis) ⭐核心差异化步骤

> 淘汰赛第一因子。排名差无法解释 2022克罗地亚(12)淘汰巴西(1)、摩洛哥(22)淘汰西班牙(7)/葡萄牙(9)，但特质匹配完美解释。本步骤识别比赛"风格剧本"，决定比赛走向与决胜方式。

根据两队 team_traits 组合，识别4种剧本：

**剧本A：强攻 vs 铁桶 (ATTACK_VS_FORTRESS)**

```
触发: 一方 counter_attack_eff<=2 且 defensive_resilience<=2 (纯进攻型)
      另一方 defensive_resilience>=4 (铁血防守型)
2022案例: 巴西vs克罗地亚、西班牙vs摩洛哥

attack_power = MAX(进攻方 counter_attack, set_piece, 3)
defense_power = 防守方 defensive_resilience
IF attack_power >= defense_power + 2: outcome=FAVORED_WIN_90MIN; et_prob=0.20
ELIF attack_power >= defense_power:    outcome=LIKELY_EXTRA_TIME; et_prob=0.60
                                       IF 防守方 penalty_track>=4: penalty_upset_boost=+0.12
ELSE:                                  outcome=UPSET_RISK_HIGH; et_prob=0.50; upset_boost=+0.15
```

**剧本B：双强对攻 (DUAL_ATTACK)**

```
触发: 双方 defensive_resilience<=3
2022案例: 阿根廷vs法国(决赛); 2018案例: 法国vs阿根廷(4-3)、巴西vs比利时
IF 一方 star_player_dep>=4 AND comeback_gene>=4: slight_edge=该方
ELSE: slight_edge=NEITHER
et_prob=0.35; draw_90min=0.30
v1.2: IF 一方 counter_attack_efficiency>=5 → 该方 favored_win_adjust +=0.04 (顶级反击在对攻中是决定性武器)
      // 2018比利时counter5淘汰巴西、2022法国counter5(姆巴佩)淘汰英格兰的跨届验证
```

**剧本C：稳健对稳健 (MUTUAL_SOLIDITY)**

```
触发: 双方 defensive_resilience>=4
2022案例: 摩洛哥vs葡萄牙(QF)
outcome=LOW_SCORING; et_prob=0.40; draw_90min=0.35
slight_edge = 反击更致命的一方(counter_attack_eff 更高者)
```

**剧本D：实力悬殊 (CLEAR_GAP)**

```
触发: 不满足以上且 rank_diff>=15
2022案例: 英格兰vs塞内加尔(3-0)、葡萄牙vs瑞士(6-1)
IF rank_diff>=25: outcome=STRONG_FAVORITE; et_prob=0.10
ELSE:             outcome=MODERATE_FAVORITE; et_prob=0.25
```

**输出**：`{ step: 4, match_script: { type, outcome, slight_edge, narrative }, extra_time_probability, penalty_probability: et_prob*0.83, trait_driven_adjustments: { upset_boost, draw_boost, favored_win_adjust } }`

---

### STEP 5: 加时/点球决胜预测 (Extra Time & Penalty Prediction)

> 淘汰赛允许90分钟平局，但必须决出晋级者。本步骤预测"平局后的最终胜者与决胜方式"。**触发条件**：STEP 2/4 判定 draw≥0.28 OR 剧本为 ATTACK_VS_FORTRESS OR stage==FINAL。否则跳过（晋级=90分钟胜方）。

**加时赛预测**（2022+2018规律：加时赛中防守韧性+逆转基因+大赛经验决定，加时内解决率=0%）：

```
home_et = defensive_resilience*0.4 + comeback_gene*0.3 + tournament_experience*0.3
away_et = 同
diff = home_et - away_et
IF diff > 0.5:  et_winner=HOME;  et_settle_prob=0.30+diff*0.05
ELIF diff < -0.5: et_winner=AWAY; et_settle_prob=0.30+|diff|*0.05
ELSE: et_winner=TOO_CLOSE; et_settle_prob=0.15  // 大部分进点球
```

**点球大战预测**（门将能力>大赛经验>心理）：

```
home_pen = penalty_track_record*0.4 + tournament_experience*0.3 + comeback_gene*0.3
away_pen = 同
pen_diff = home_pen - away_pen
IF pen_diff >= 1.0: pen_winner=HOME; pen_conf=0.60+pen_diff*0.05
ELIF pen_diff <= -1.0: pen_winner=AWAY; pen_conf=0.60+|pen_diff|*0.05
ELSE: 接近抛硬币, pen_winner=差距正负方向; pen_conf=0.52
key_factor = goalkeeper_advantage | experience_advantage | mental_toughness | coin_flip
```

**输出**：`{ step: 5, triggered, extra_time_probability, penalty_probability, if_extra_time: {predicted_winner, settle_in_et_probability}, if_penalty: {predicted_winner, confidence, key_factor} }`

---

### STEP 6: 阶段独立综合概率合成 (Stage Synthesis)

> 将 STEP 1-5 合成为"90分钟赛果"与"晋级预测"双层结果。

#### Part A: 90分钟结果

```
// 基线 = STEP 1 双支柱基线（已含小组赛表现+stage_correction）
W = step1.W; D = step1.D; L = step1.L

// STEP 3 心理韧性修正
W += mental_adjust_dir; (双向)

// STEP 2 爆冷修正（按剧本分流）
IF step4.match_script.type == ATTACK_VS_FORTRESS AND 防守方为弱队:
    // 爆冷信号优先进入平局/弱队胜
    // v1.2: 顶级零封铁桶(clean_sheets>=2)有90min直接取胜能力，L权重提升
    IF 弱队 clean_sheets >= 2:
        D += step2.final_upset_boost * 0.4; L += step2.final_upset_boost * 0.4  // 2022摩洛哥vs葡萄牙(1-0胜)校准
    ELSE:
        D += step2.final_upset_boost * 0.5; L += step2.final_upset_boost * 0.3
ELIF step4.match_script.type == CLEAR_GAP:
    L += step2.final_upset_boost * 0.3   // 悬殊局弱队偶爆冷
ELSE:
    L += step2.final_upset_boost * 0.5
    D += step2.final_upset_boost * 0.3

// STEP 4 特质剧本修正（QF阶段 trait_multiplier=1.3）
trait_mult = (stage==QF) ? 1.3 : 1.0
W += trait_driven.favored_win_adjust * trait_mult * direction
L += trait_driven.upset_boost * trait_mult * direction
D += trait_driven.draw_boost * trait_mult

// 阶段平局基线修正（淘汰赛高平局，v1.2 微调）
D += stage_draw_baseline[stage]   // R32+0.00, R16+0.03(v1.2从0.02提升), QF+0.04, SF+0.04(v1.2从0.02提升), 3RD+0.00, FINAL+0.06

// 归一化 + 边界保护(>=5%)
confidence_90 = HIGH if max>=0.50 else MEDIUM if max>=0.38 else LOW
```

#### Part B: 晋级预测（含加时/点球分支）

```
advance_home = final_W (90分钟主胜)
advance_away = final_L (90分钟客胜)
draw_case = final_D

IF step5.triggered:
    // 平局分支的晋级分配
    IF step5.et_winner == HOME:
        advance_home += draw_case * et_settle_prob
        remain = draw_case * (1 - et_settle_prob)
        advance_home += remain * pen_conf * (pen_winner==HOME?1:0)
        advance_away += remain * pen_conf * (pen_winner==AWAY?1:0)
    ELIF et_winner == AWAY: (方向相反)
    ELSE: // TOO_CLOSE，大概率点球
        advance_home += draw_case * pen_conf * (pen_winner==HOME?1:0)
        advance_away += draw_case * pen_conf * (pen_winner==AWAY?1:0)
ELSE:
    // 加时概率低，默认排名更优方略占优
    favored_et = rank 更优方
    advance_{favored} += draw_case * 0.55
    advance_{other} += draw_case * 0.45

advancing_team = advance_home>advance_away ? home : away
method_probabilities = { settle_in_90min: final_W+final_L, settle_in_et: ..., settle_in_penalty: ... }
predicted_method = 概率最高者
```

**输出**：`{ step: 6, prediction_90min: {result, probabilities, confidence}, prediction_advance: {advancing_team, advance_probability, predicted_method, method_probabilities} }`

---

### STEP 6.5: 阶段差异化比分推荐 (Stage-Differentiated Score)

#### 6.5.1 预期进球 (xG)

```
xG_favored  = 1.3 + (rank_diff / 100) * 0.6
xG_underdog = 0.7 + (final_upset / 0.30) * 0.5

// 阶段修正
R32:  xG_total *= 1.10 (强弱悬殊大球)
QF:   xG_total *= 0.90 (黑马局低消耗)
3RD:  xG_total *= 1.15 (开放局)
FINAL:xG_total *= 0.95 (保守)
```

#### 6.5.2 Poisson 比分矩阵 + 阶段筛选

```
P(i,j) = Poisson(xG_favored,i) × Poisson(xG_underdog,j), i,j ∈ [0,5]
按结果分组归一化到 STEP 6 的三分概率
```

**阶段差异化 Top5 筛选**：

- **R32（硬实力碾压）**：3 强队胜 + 1 平局 + 1 爆冷 | 范围扩展至[0,6]覆盖大比分
- **R16（特质猎手）**：按剧本——ATTACK_VS_FORTRESS → 2 平局 + 2 强队胜 + 1 爆冷；CLEAR_GAP → 3 强队胜 + 1 平 + 1 爆冷
- **QF（黑马猎手）**：防守剧本 → 3 平局(0-0,1-1) + 1 黑马胜 + 1 强队胜；xG_total×0.90
- **SF（实力回归）**：3 强队胜 + 1 平局 + 1 爆冷
- **3RD（经验猎手）**：3 大球胜 + 1 平局 + 1 爆冷 | xG_total×1.15
- **FINAL（心理猎手）**：2 平局(0-0,1-1) + 2 强队胜 + 1 爆冷 | xG_total×0.95

#### 6.5.3 总进球数区间 + BTTS

```
"0-1_goals": Poisson(xG_total,0)+Poisson(xG_total,1)
"2-3_goals": Poisson(xG_total,2)+Poisson(xG_total,3)
"4+_goals":  1 - sum(above)
BTTS_YES = (1-Poisson(xG_favored,0)) × (1-Poisson(xG_underdog,0))
```

**爆冷预警**：

```
// 全爆冷（弱队胜）
IF final_upset >= 0.30 → full_upset_level = STRONG
IF final_upset >= 0.22 → full_upset_level = MODERATE
// 拖入决胜爆冷（弱队平+点球晋级）
IF rank_diff >= 10 AND final_draw >= 0.30 AND 弱队 penalty_track>=4 → decider_upset_level = STRONG
upset_alert.level = max(full, decider)
upset_alert.type = FULL_UPSET | DECIDER_UPSET | BOTH | NONE
```

---

## 最终输出规范 (Output Schema)

```json
{
  "match_id": "string", "stage": "string",
  "prediction_90min": {
    "result": "favored_win | draw | upset",
    "confidence": "HIGH | MEDIUM | LOW",
    "probabilities": { "favored_win": "float", "draw": "float", "upset": "float" },
    "favored_team": "string", "underdog_team": "string"
  },
  "prediction_advance": {
    "advancing_team": "string", "advance_probability": "float",
    "eliminated_team": "string",
    "predicted_method": "IN_90MIN | IN_EXTRA_TIME | IN_PENALTY",
    "method_probabilities": { "settle_in_90min": "float", "settle_in_extra_time": "float", "settle_in_penalty": "float" }
  },
  "stage_strategy_profile": {
    "strategy_mode": "STRENGTH_CRUSHER | TRAIT_HUNTER | DARK_HORSE_HUNTER | STRENGTH_REGRESSION | EXPERIENCE_HUNTER | PSYCHOLOGY_HUNTER",
    "stage_upset_multiplier": "float", "stage_correction": "float", "stage_draw_baseline": "float",
    "strategy_signals": {
      "hard_strength_signal": "STRONG|MODERATE|WEAK (双支柱硬实力)",
      "group_form_signal": "STRONG|MODERATE|WEAK (当年小组赛表现)",
      "upset_signal": "STRONG|MODERATE|WEAK",
      "trait_script": "ATTACK_VS_FORTRESS|DUAL_ATTACK|MUTUAL_SOLIDITY|CLEAR_GAP",
      "decider_signal": "DETECTED|NOT_DETECTED (加时/点球倾向)"
    },
    "recommended_scores": {
      "primary": [{ "score": "string", "probability": "float", "result_type": "string" }],
      "secondary": [{ "score": "string", "probability": "float", "result_type": "string" }]
    }
  },
  "upset_alert": {
    "triggered": "boolean", "level": "STRONG|MODERATE|NONE",
    "type": "FULL_UPSET|DECIDER_UPSET|BOTH|NONE", "reasoning": "string"
  },
  "analysis_trace": {
    "step1_dual_pillar": "object (含 gspi_home/away, signal_conflict, base_probabilities, stage_correction)",
    "step2_upset_pattern": "object",
    "step3_psychology": "object (含 mti_home/away, mental_adjust)",
    "step4_trait_matchup": "object",
    "step5_extra_time_penalty": "object|null"
  }
}
```

---

## 关键分析因子权重（阶段策略版）

| 因子 | 权重 | 策略作用 |
|------|------|---------|
| **硬实力（FIFA排名+小组赛表现双支柱）** | **38%** | 淘汰赛第一因子——单场定胜负，硬实力权重显著高于小组赛 |
| 特质匹配（STEP 4） | 25% | QF阶段×1.3，决定比赛剧本与决胜方式 |
| 心理韧性（经验/逆转/点球） | 15% | 越靠后阶段权重越高（3RD/FINAL） |
| 阶段压力修正 | 10% | QF黑马巅峰、SF回归实力 |
| 加时/点球能力 | 7% | 影响"晋级预测"与决胜方式，不直接影响90分钟 |
| 实时数据（伤病/状态） | 5% | 保持 |

---

## 赛制适配指南 (Tournament Adaptation Guide)

### 2018 俄罗斯世界杯回测配置

```yaml
tournament_config_override:
  host_count: 1
  has_third_place_qualified: false      # STEP 1.3 第3名折损跳过
  champion_match_count: 7
# 阶段: R16(1/8)→QF→SF→3RD→FINAL（无R32，2018淘汰赛从16强开始）
# 特殊修正:
#   东道主(俄罗斯#70): HOST_FORTRESS 模式 + favored_win += 0.06（贯穿整届）
#   卫冕冠军(德国): 已小组出局，不参与淘汰赛
#   info_clarity: 不适用（淘汰赛对阵已锁定）
```

### 2022 卡塔尔世界杯回测配置

```yaml
tournament_config_override:
  host_count: 1
  has_third_place_qualified: false
  champion_match_count: 7
# 特殊修正:
#   5换人规则: upset_boost *= 1.15（弱队体能劣势缩小，利好防守反击黑马）
#   AFC球队: 防守型黑马信号中 AFC 来源额外 +0.02（日本/韩国淘汰赛韧性）
#   东道主(卡塔尔#50): 小组出局，不参与；HOST_FORTRESS 不触发
#   卫冕冠军(法国#4): 打破魔咒进决赛，衰退检测不触发
```

### 2026 美加墨世界杯配置

```yaml
tournament_config:
  host_count: 3                         # 美/加/墨，东道主效应待评估（非传统弱东道主）
  has_third_place_qualified: true       # 8个小组第3名进R32
  champion_match_count: 8               # 比2018/2022多1场R32，阵容深度更重要
# 新增:
#   STEP 1.3 R32 第3名折损: group_position==3 → favored_win*0.80
#   STEP 3 SF 体能考: 多1场R32消耗，squad_depth权重上调
#   阵容深度(squad_depth)因子权重从隐含升至显式（8场消耗）
```

### 回测执行流程

1. **数据准备**: 读取 `data/{year}_FIFA_World_Cup_Results.md` 淘汰赛部分，提取双方 FIFA 排名、小组赛汇总、逐场90分钟/加时/点球结果
2. **逐场预测**: 对 R16→QF→SF→3RD→FINAL 每场独立执行本 skill（隔离单步误差，不传导预测结果）
3. **命中率统计**: 90分钟方向命中、晋级命中、爆冷预警命中、加时/点球预测命中、比分Top5覆盖
4. **经验提取**: 识别赛制无关的通用规律（防守型黑马规则、阶段爆冷/平局系数、心理韧性阈值），校准参数
5. **反哺2026**: 将校准参数更新到2026版本默认值

### 经验反哺维度

| 维度 | 提取方法 | 反哺目标参数 |
|------|---------|------------|
| 各阶段爆冷率偏差 | 预测vs实际爆冷率 | stage_upset_multiplier |
| 各阶段平局率偏差 | 预测vs实际90min平局率 | stage_draw_baseline |
| 防守型黑马识别有效性 | 触发后实际爆冷/晋级比例 | DEFENSIVE_DARK_HORSE 触发门槛与 base_upset_boost |
| 双支柱基线有效性 | 小组赛表现修正后的方向命中率 | signal_diff 权重(0.5/0.8) |
| 加时/点球预测命中 | 预测进入加时且实际进入的比例 | STEP 5 触发阈值 |
| 比分Top5覆盖 | 实际比分落入Top5比例 | Poisson xG 阶段修正 |
| **连续加时体能（v1.2）** | 连续加时方在SF/Final的实际胜率 | consecutive_et_penalty (STEP 1.5) |
| **DUAL_ATTACK反击（v1.2）** | counter≥5方在对攻剧本的胜率 | counter_attack_efficiency 额外加权 |
| **东道主累积（v1.2）** | 东道主连续爆冷的递增效应 | HOST_FORTRESS 累积+0.05/场 |

---

## 回测验证结果摘要（v1.1 已校准参数）

**2018 回测**（16场淘汰赛，详见 `knockout_stage_round_strategy-2018_backtest.md`）：

| 指标 | 结果 |
|------|------|
| 90分钟方向命中 | 10/16 = 62.5% |
| 晋级队伍命中 | 12/16 = 75.0% |
| 爆冷预警命中 | 2/3 = 66.7%（俄罗斯淘汰西班牙 STRONG 命中） |
| 加时/点球预测命中 | 3/5 = 60.0% |
| 比分Top5覆盖 | 8/16 = 50.0% |
| 亮点 | 连续加时体能考在决赛决定性翻转（克罗地亚-0.18→法国方向胜）、双支柱势头覆盖（法国胜阿根廷/乌拉圭胜葡萄牙）、哥伦比亚vs英格兰均势平局捕获 |
| 不足 | 5场平局仅捕获1场（近均势倾向预测胜）、东道主rank悬殊爆冷方向难翻、近均势coin-flip区分力不足 |

> **2018 难度说明**：2018是平局密集型赛事（5场90min平局/31.25%），3场涉及东道主俄罗斯。90min方向命中率(62.5%)低于2022(87.5%)，但连续加时体能考的核心价值（决赛翻转方向）是本届最重要发现。

**2022 回测**（16场淘汰赛，详见 `knockout_stage_round_strategy-2022_backtest.md`）：

| 指标 | 结果 |
|------|------|
| 90分钟方向命中 | 14/16 = 87.5% |
| 晋级队伍命中 | 15/16 = 93.75% |
| 爆冷预警命中 | 3/3 = 100%（摩洛哥×2、克罗地亚全命中） |
| 加时/点球预测命中 | 5/6 = 83.3% |
| 比分Top5覆盖 | 10/16 = 62.5% |
| 亮点 | 摩洛哥淘汰西班牙/葡萄牙（DEFENSIVE_DARK_HORSE 标杆）、克罗地亚点球淘汰巴西、5场平局全捕获、点球大战预测5/5全中 |
| 不足 | 摩洛哥vs葡萄牙90min方向（预测平局实际1-0胜）、英格兰vs法国DUAL_ATTACK反击权重不足 |

> **2022 优势说明**：2022淘汰赛高度模式化（防守型黑马+点球大战主旋律），策略的 DEFENSIVE_DARK_HORSE+PENALTY_SPECIALIST+DECIDER 三机制达到最大价值。晋级预测93.75%的高命中率直接受益于点球大战预测5/5全中（门将能力评估）。

**双支柱硬实力基线有效性验证（跨届）**：
- 2018：3支小组赛PERFECT球队(乌拉圭/克罗地亚/比利时, GSPI+0.14)淘汰赛方向预测全部受益；GSPI-rank冲突覆盖4场(法国胜阿根廷/乌拉圭胜葡萄牙等)方向3/4正确
- 2022：GSPI修正使4场方向更准，2场冲突覆盖(日本vs克罗地亚/英格兰vs法国)方向正确
- **核心结论**：当年小组赛表现(GSPI)是淘汰赛开战时最准的实时实力代理，专门修正FIFA排名失真——双支柱基线使"排名失真"类球队方向命中率提升约12-15%

**阶段爆冷/平局系数校准依据**：

| 阶段 | 实际爆冷率 | 实际平局率 | 校准后系数（v1.2） |
|------|-----------|-----------|-----------|
| R16 | 12.5% | 25% | upset_mult=1.0, draw_base=**+0.03**(v1.2从0.02提升) |
| QF | 25% | 37.5% | upset_mult=1.4, draw_base=+0.04 |
| SF | 25% | 25% | upset_mult=0.7, draw_base=**+0.04**(v1.2从0.02提升) |
| FINAL | 0% | 50% | upset_mult=0.8, draw_base=+0.06 |

---

## 使用说明

1. **独立使用**: 本文件完全自包含，可直接交给具备 web search 能力的大模型使用
2. **与原模型关系**: 本文件是 `knockout_stage_predict.md` 的阶段策略定制版，原模型中与本文件冲突的逻辑以本文件为准；原模型的特质匹配(STEP 2)与加时/点球(STEP 4)框架被继承并增强
3. **数据流位置**: group_stage_round_strategy(小组赛) → **本文件(淘汰赛单场)** → championship_predict(冠亚军)。本文件消费小组赛输出的 `group_stage_output`（STEP 0.5 阶段二）
4. **逐场执行**: 对每场淘汰赛独立运行本 skill，执行顺序见「推理步骤链」
5. **数据文件依赖**: STEP 0.5 需读取 `data/2026_FIFA_World_Cup_Round_of_32.md`（淘汰赛对阵+FIFA排名）与 `data/2026_FIFA_World_Cup_Group_Stage.md`（小组赛汇总回灌 group_stage_output）。**维护责任**：小组赛全部结束后需将各组最终积分/净胜球/势头/零封完整回填，这是淘汰赛"当年小组赛表现"支柱的硬前提
6. **2026新增 R32 注意**: R32 涉及8个小组第3名出线队，STEP 1.3 的第3名折损(favored_win*0.80)仅在 R32 触发；这些第3名若 FIFA排名≤10 触发"死亡之组特赦"（继承冠亚军分析策略四），抹除折损并 +0.05 背水一战激励

---

*基于2018年俄罗斯世界杯和2022年卡塔尔世界杯32场淘汰赛数据设计，适配2026年美加墨世界杯赛制*
*版本1.2 — 派生自 knockout_stage_predict v1.0，阶段差异化策略引导；双支柱硬实力基线（FIFA排名+当年小组赛表现），删除小组赛专属步骤（名次博弈/第3名出线/路径选择），强化特质匹配与加时/点球决胜；v1.2 经2018+2022双回测反哺（连续加时体能正式化、防守黑马门槛放宽、DUAL_ATTACK反击加权、东道主累积效应）*
