# Skill: group_stage_predict — 小组赛单场预测

## 元信息

- **版本**: 2.1
- **适用赛制**: 2026年世界杯小组赛（48队 / 12组 / 每组4队 / 前2名+8个最好第3名出线）
- **分析粒度**: 单场比赛胜负预测 + 比分概率 + 进球分布
- **核心定位**: 赛制约束与博弈
- **使用方式**: 本文件为自包含 prompt，既可嵌入项目通过 API 调用，也可直接交给任何具备 web search 能力的大模型独立执行
- **下游消费者**: knockout_stage_predict（淘汰赛预测）、championship_predict（冠亚军预测）

---

## 输入规范 (Input Schema)

```json
{
  "match": {
    "match_id": "string — 唯一标识符，如 'A_M1'",
    "group": "string — 组别 A-L",
    "round": "integer — 轮次 1-3",
    "home_team": "string — 主队名称",
    "away_team": "string — 客队名称"
  },
  "teams": {
    "<team_name>": {
      "fifa_ranking": "integer — 赛前FIFA世界排名（必填）",
      "world_cup_experience": "integer — 历史世界杯参赛次数（必填）",
      "confederation": "string — 所属洲际足联 UEFA/CONMEBOL/AFC/CAF/CONCACAF/OFC（必填）"
    }
  },
  "group_context": {
    "teams_in_group": ["string — 组内4队名称列表"],
    "completed_matches": [
      {
        "match_id": "string",
        "home": "string",
        "away": "string",
        "score": "string — 如 '2-1'",
        "result": "string — 'home_win' | 'draw' | 'away_win'"
      }
    ]
  },
  "tournament_context": {
    "other_groups_completed_matches": "object — 其他组已完赛结果（用于第3名出线概率估算）"
  },
  "tournament_config": {
    "teams_per_group": 4,
    "matches_per_team": 3,
    "advance_top_n": 2,
    "best_third_advance_count": 8,
    "total_groups": 12,
    "advancement_rate": 0.667
  }
}
```

---

## 淘汰赛对阵参考数据 (Knockout Bracket Reference)

> 以下数据供 STEP 6 使用。基于 FIFA 官方公布的 2026 世界杯淘汰赛对阵结构。同组第1名和第2名被分入不同半区，只有决赛才能相遇。

### 上半区 (SF_01 路径 → 决赛 pos=1)

| R32 比赛 | 对阵 | → R16 | → QF | → SF |
|---------|------|-------|------|------|
| R32_03 (M74) | E1 vs 3rd(A/B/C/D/F) | R16_01 | QF_01 | SF_01 |
| R32_06 (M77) | I1 vs 3rd(C/D/F/G/H) | R16_01 | | |
| R32_01 (M73) | A2 vs B2 | R16_02 | QF_01 | |
| R32_04 (M75) | F1 vs C2 | R16_02 | | |
| R32_12 (M83) | K2 vs L2 | R16_05 | QF_02 | |
| R32_11 (M84) | H1 vs J2 | R16_05 | | |
| R32_10 (M81) | D1 vs 3rd(B/E/F/I/J) | R16_06 | QF_02 | |
| R32_09 (M82) | G1 vs 3rd(A/E/H/I/J) | R16_06 | | |

### 下半区 (SF_02 路径 → 决赛 pos=2)

| R32 比赛 | 对阵 | → R16 | → QF | → SF |
|---------|------|-------|------|------|
| R32_02 (M76) | C1 vs F2 | R16_03 | QF_03 | SF_02 |
| R32_05 (M78) | E2 vs I2 | R16_03 | | |
| R32_07 (M79) | A1 vs 3rd(C/E/F/H/I) | R16_04 | QF_03 | |
| R32_08 (M80) | L1 vs 3rd(E/H/I/J/K) | R16_04 | | |
| R32_15 (M86) | J1 vs H2 | R16_07 | QF_04 | |
| R32_14 (M88) | D2 vs G2 | R16_07 | | |
| R32_13 (M85) | B1 vs 3rd(E/F/G/I/J) | R16_08 | QF_04 | |
| R32_16 (M87) | K1 vs 3rd(D/E/I/J/L) | R16_08 | | |

### 半区分布速查

> 同组第1名和第2名被分入不同半区，只有决赛才能相遇。

| 小组 | 第1名→R32 | 第2名→R32 | | 小组 | 第1名→R32 | 第2名→R32 |
|------|----------|----------|-|------|----------|----------|
| A | 下 R32_07 | 上 R32_01 | | G | 上 R32_09 | 下 R32_14 |
| B | 下 R32_13 | 上 R32_01 | | H | 上 R32_11 | 下 R32_15 |
| C | 下 R32_02 | 上 R32_04 | | I | 上 R32_06 | 下 R32_05 |
| D | 上 R32_10 | 下 R32_14 | | J | 下 R32_15 | 上 R32_11 |
| E | 上 R32_03 | 下 R32_05 | | K | 下 R32_16 | 上 R32_12 |
| F | 上 R32_04 | 下 R32_02 | | L | 下 R32_08 | 上 R32_12 |

### 第三名候选来源约束

| R32 比赛 | 种子队 | 第三名候选来源组 | | R32 比赛 | 种子队 | 第三名候选来源组 |
|---------|--------|----------------|-|---------|--------|----------------|
| R32_03 | E1 | A/B/C/D/F | | R32_09 | G1 | A/E/H/I/J |
| R32_06 | I1 | C/D/F/G/H | | R32_10 | D1 | B/E/F/I/J |
| R32_07 | A1 | C/E/F/H/I | | R32_13 | B1 | E/F/G/I/J |
| R32_08 | L1 | E/H/I/J/K | | R32_16 | K1 | D/E/I/J/L |

---

## 推理步骤链 (Reasoning Chain)

执行顺序：STEP 0 → STEP 1 → STEP 2 → STEP 3 → STEP 4 → STEP 5 → STEP 5.5 → STEP 6

---

### STEP 0: 实时数据获取 (Realtime Data Acquisition)

**目标**：在推理前主动搜索并收集双方球队的最新情报，为后续步骤提供实时修正依据。

**执行指令**：

> 你必须使用可用的搜索工具（web search / browser / API），针对本场比赛的双方球队主动获取以下实时数据。如果工具不可用，则基于你的知识库中最新的信息进行分析，并在输出中标注 `data_source: "knowledge_cutoff"`。

**必搜清单**（按优先级排序）：

| 优先级 | 搜索目标 | 搜索关键词示例 | 用途 |
|--------|---------|---------------|------|
| P0 | 双方近5场正式比赛成绩 | `"{{team}} 最近5场比赛结果"` | STEP 2 状态修正 |
| P0 | 核心球员伤病/停赛情况 | `"{{team}} 伤病名单 {{year}}"` | STEP 2 爆冷修正 |
| P1 | 赛前主帅发言/轮换暗示 | `"{{team}} 主教练 采访 轮换 {{match_date}}"` | STEP 3 动机修正 |
| P1 | 双方历史交锋记录 | `"{{home}} vs {{away}} 历史交锋"` | STEP 1 基线校准 |
| P2 | 赛前赔率/预测市场数据 | `"{{home}} vs {{away}} 赔率 预测"` | STEP 5 结果校验 |
| P2 | 其他小组出线形势（第三轮适用） | `"2026世界杯 {{group}}组 出线形势"` | STEP 4 第3名概率 |

**数据整理格式**（搜索完成后自行整理为以下结构供后续步骤引用）：

```
realtime_data = {
  {{home_team}}: {
    recent_form: "近5场结果，如 W-W-D-L-W",
    recent_goals_for: int, recent_goals_against: int,
    key_injuries: [{player, position, impact: HIGH|MEDIUM|LOW}],
    coach_intent: "赛前关键叙事（轮换/全主力/试验阵型等）",
    data_source: "web_search | knowledge_cutoff",
    data_date: "搜索日期"
  },
  {{away_team}}: { ... 同结构 ... },
  h2h: "近期交锋简述",
  market_odds: { home_win: float, draw: float, away_win: float } | null
}
```

**搜索质量校验**：
- 如果关键数据（P0 项）无法获取，需在最终输出的 `confidence` 中降一级（HIGH→MEDIUM→LOW）
- 如果所有数据均来自知识库而非实时搜索，需在 `narrative` 中明确标注

---

### STEP 1: 实力基线评估 (Base Strength Assessment)

---

### STEP 1: 实力基线评估 (Base Strength Assessment)

**目标**：基于FIFA排名差计算基础胜/平/负概率。

**执行指令**：

```
1. 计算 rank_diff = |home.fifa_ranking - away.fifa_ranking|
2. 识别优势方：favored_team = 排名更靠前的队，underdog_team = 另一队
3. 查表获取基础概率：
```

| 排名差区间 | favored_win | draw | upset |
|-----------|-------------|------|-------|
| 0-5 | 0.40 | 0.35 | 0.25 |
| 6-15 | 0.48 | 0.28 | 0.24 |
| 16-30 | 0.55 | 0.25 | 0.20 |
| 31-45 | 0.65 | 0.20 | 0.15 |
| >45 | 0.73 | 0.15 | 0.12 |

**2022特殊修正**（匹配以下条件时叠加到 upset）：
- 弱队 FIFA 排名 15-30 且来自 AFC/CAF/CONCACAF：upset +0.08（中游非欧强队爆冷模式，2022 日本/摩洛哥案例）
- 弱队 FIFA 排名 15-30 且 `world_cup_experience >= 5`：upset +0.05（大赛经验加成）

**输出**：

```json
{
  "step": 1,
  "rank_diff": "integer",
  "favored_team": "string",
  "underdog_team": "string",
  "base_probabilities": {
    "favored_win": "float",
    "draw": "float",
    "upset": "float"
  }
}
```

---

### STEP 2: 爆冷模式识别 (Upset Pattern Detection)

**目标**：判断弱队如果爆冷，最可能采用的模式及成功概率提升。

**执行指令**：

```
1. 取 STEP 1 的 underdog_team 及其 fifa_ranking
2. 按弱队排名区间匹配爆冷模式：
```

| 弱队排名区间 | 模式标识 | 特征 | upset_boost | 2022案例 |
|-------------|---------|------|------------|---------|
| ≤25 | TACTICAL_STRETCH | 主动放弃控球、快速转换、利用强队压上空间 | +0.08 | 日本胜德国/西班牙 |
| 26-40 | SOLID_DEFENSE | 低位防守、减少失误、利用定位球或零星反击 | +0.04 | 澳大利亚胜丹麦 |
| >40 | DESPERATE_BURST | 全员退守+偶然进球，或利用强队轮换 | +0.02 | 沙特胜阿根廷 |

**附加修正**：
- 弱队 `world_cup_experience >= 5`：TACTICAL_STRETCH 额外 +0.05（大赛经验加成）
- 强队已锁定出线 + DESPERATE_BURST → 触发 ROTATION_EXPLOIT 子模式，额外 +0.06

**实时数据修正**（引用 STEP 0 的 `realtime_data`）：
- 对方 `key_injuries` 中有 impact=HIGH 的 FW 或核心 MF：upset_boost +0.03
- 弱队 `recent_form` 胜率 ≥ 60%：upset_boost +0.02
- 强队 `coach_intent` 提到"轮换"/"休息"：ROTATION_EXPLOIT 额外 +0.03

**输出**：

```json
{
  "step": 2,
  "underdog_pattern": "TACTICAL_STRETCH | SOLID_DEFENSE | DESPERATE_BURST",
  "upset_boost": "float — 叠加到基础爆冷概率上",
  "pattern_confidence": "float 0.0-1.0"
}
```

---

### STEP 3: 策略性动机分析 (Strategic Motivation Analysis) ⭐核心步骤

**目标**：识别"强队不全力争胜"的场景，量化动机差异，输出概率调整系数。

**2026赛制背景**：出线率66.7%（32/48），强队输球淘汰代价极低。2022第3轮8场中4场强队明确放水（50%），2026此效应将更频繁。

#### 3.1 出线安全度 (ASS, Advancement Safety Score)

取值范围：0.0 ~ 1.0

**第一轮**：`rank_group` = 球队在本组4队中的FIFA排名序号（1=最强，4=最弱）

```
rank_group=1 → ASS=0.85 | rank_group=2 → ASS=0.65 | rank_group=3 → ASS=0.40 | rank_group=4 → ASS=0.20
```

**第二轮**（首轮结果已出）：

```
points=3: ASS = 0.80 + (rank_group==1 ? 0.10 : 0.00)
points=1: ASS = 0.45 + (rank_group<=2 ? 0.15 : 0.00)
points=0: ASS = 0.15 + (rank_group<=2 ? 0.20 : 0.00)
```

**第三轮**（精确计算）：

```
points>=6: ASS=0.98+ | points=4: ASS=0.80-0.95 | points=3: ASS=0.30-0.60
points=1: ASS=0.05-0.20 | points=0: ASS=0.00-0.02
注：第三轮需结合 STEP 4 的第3名出线概率精确计算
```

#### 3.2 动机差异指数 (MDI) 与调整系数 (MAF)

```
MDI = Motivation_self - Motivation_opponent
Motivation = 1.0 - ASS * (1 - urgency)

urgency: 必须赢=1.0 | 不赢也可能出线=0.7 | 平局即可=0.5 | 已锁定=0.1 | 已出局=0.0

MAF = abs(MDI) * 0.25 * round_weight * safety_amplifier
round_weight: R1=0.6 | R2=0.8 | R3=1.0
safety_amplifier: (ASS_self>0.90 AND ASS_opponent<0.30) ? 1.5 : 1.0
MAF 上限 = 0.35
```

**实时叙事修正**（引用 STEP 0 的 `realtime_data`）：
- `coach_intent` 明确提到"轮换"/"休息"：urgency *= 0.7（大幅降低求胜欲）
- 对方有 2+ 名 HIGH impact 球员缺阵：Motivation_self += 0.10（信心增强）

#### 3.3 按轮次触发条件

**第一轮**：R1-A: 排名差>25 且弱队 rank_group=3/4 → 弱队动机+0.15 | R1-B: rank_group=1 且 ASS>0.80 → 强队不全主力 | R1-C: 同组另一场已出结果且爆冷 → 动态重算 ASS

**第二轮**：R2-SL(3vs0) 风险最高（MAF≈0.10，MDI=-0.425，强队胜率下调约10%）| R2-SW(3vs1) 中风险 | 其他场景 ≈0

**第三轮**：R3-A: ASS≥0.95 → Motivation=0.1, MAF=0.20-0.35 | R3-B: 双方平局后均达4分 → 平局概率+15-25% | R3-C: 输球仍可能第3名出线 → 调用 STEP 4 | R3-D: ASS>0.80 且可能第1 → 调用 STEP 6

**R3-D 时间序列博弈**：第三轮开球时间线 `B→C→A→E→F→D→I→H→G→L→K→J`，越靠后掌握越多落位情报。本组位于后半段（G/L/K/J）时：`urgency *= info_clarity (info_clarity = group_index / 11.0)`

#### 3.4 概率修正公式

```
输入：W_base, D_base, L_base（STEP 1-2 输出），MAF, MDI

if MDI > 0（己方动机更强）:
    W_adj = W_base + MAF * (1 - W_base)
    L_adj = L_base * (1 - MAF)
elif MDI < 0（对手动机更强）:
    L_adj = L_base + MAF * (1 - L_base)
    W_adj = W_base * (1 - MAF)

D_adj = 1.0 - W_adj - L_adj

# 默契球叠加（R3-B 触发时）
if tacit_draw_risk:
    draw_bonus = tacit_draw_risk * 0.20
    W_adj *= (1 - draw_bonus)
    L_adj *= (1 - draw_bonus)
    D_adj = 1.0 - W_adj - L_adj

# 边界保护（最低5%，防止极端值）
W_adj = MAX(0.05, W_adj)
D_adj = MAX(0.05, D_adj)
L_adj = MAX(0.05, L_adj)

# 归一化
total = W_adj + D_adj + L_adj
W_final = W_adj / total
D_final = D_adj / total
L_final = L_adj / total
```

#### 3.5 边界情况处理

| 边界情况 | 处理方式 |
|---------|---------|
| 双方均已出局 | Motivation=0.1，MAF=0（净效应抵消），回归实力基线 |
| 同组另一场出现重大意外 | 动态重算 ASS，confidence 降为 "low" |
| 淘汰赛路径涉及未完赛组 | STEP 6 只给概率性评估，confidence 标记 "medium"/"low" |
| 同组两场第三轮联动 | 假设同组另一场以"最可能结果"计算，narrative 中标注假设 |
| 净胜球因素 | 净胜球优势>2时 urgency *= 0.85 |

**输出**：`{ step: 3, analysis: { ASS_self, ASS_opponent, urgency_self, urgency_opponent, MDI, MAF, round_weight, safety_amplifier }, triggers: [{trigger_id, condition_met, detail}], special_flags: { tacit_draw_risk, knockout_path_bias, third_place_probability }, adjustment: { W_adjusted, D_adjusted, L_adjusted, confidence }, narrative: { key_risk, adjustment_note } }`

---

### STEP 4: 第3名出线概率评估 (Third-Place Advancement Probability)

**目标**：评估小组第3名出线规则对本场比赛策略的影响。

**2026赛制**：12组第3名按积分>净胜球>进球排序，取前8名出线。

**第3名出线门槛**：

| 积分 | 出线概率 | 说明 |
|------|---------|------|
| 4分（1胜1平） | >95% | 几乎必出线 |
| 3分（1胜1负） | ~50% | 取决于净胜球和其他组第3名积分 |
| 2分（2平） | 20-30% | 需其他组第3名较弱 |
| 1分（1平1负） | <5% | 几乎不可能 |

**对本场比赛的影响**：

| 场景 | 判定 | 效应 |
|------|------|------|
| 一方输球仍可能第3名出线 | 输后积分≥3 且其他组第3名预估较弱 | 该队 urgency 降低，MAF 增大 |
| 双方输球都淘汰 | 输后积分<3 或其他组第3名预估较强 | 双方极端保守或极端激进 |
| 双方都有后路 | 输后都有一定概率第3名出线 | 比赛偏开放 |

**输出**：`{ step: 4, third_place_threshold: { estimated_safety_points, confidence }, home_third_place_probability, away_third_place_probability, impact_on_match: { home_desperation_boost, away_desperation_boost, draw_boost, narrative } }`

---

### STEP 5: 综合概率合成 (Final Probability Synthesis)

**目标**：将 STEP 1-4 的输出合成为最终胜/平/负概率。

**执行指令**：

```
1. 取 STEP 3 的调整后概率作为基准（不回到 STEP 1 的 base_probabilities）：
   W = step3.adjustment.W_adjusted
   D = step3.adjustment.D_adjusted
   L = step3.adjustment.L_adjusted

2. 叠加 STEP 4 的第3名出线影响：
   根据 step4.impact_on_match 中的 desperation_boost 和 draw_boost 修正

3. 叠加 STEP 2 爆冷模式（避免与 STEP 3 双重叠加）：
   upset_mode_boost = step2.upset_boost * (1 - step3.MAF / 0.35)
   // 按 MAF 占比缩减，MAF 越大说明 STEP 3 已覆盖的爆冷效应越多

4. 归一化（确保三者之和 = 1.0）：
   total = W + D + L
   final_favored_win = W / total
   final_draw = D / total
   final_upset = L / total

5. 确定预测结果：
   max_prob = MAX(final_favored_win, final_draw, final_upset)

6. 置信度：max_prob≥0.55→HIGH | max_prob≥0.40→MEDIUM | max_prob<0.40→LOW

7. 爆冷预警：final_upset≥0.35→STRONG | final_upset≥0.25→MODERATE
```

---

### STEP 5.5: 比分概率与进球分布 (Score Probability & Goal Distribution)

**目标**：基于 STEP 5 的胜/平/负概率，推导常见比分概率和进球分布。

#### 5.5.1 预期进球数 (Expected Goals)

```
xG_favored  = 1.2 + (rank_diff / 100) * 0.8     // 范围约 1.2 ~ 2.0
xG_underdog = 0.6 + (final_upset / 0.30) * 0.6   // 爆冷概率越高，弱队威胁越大
xG_total    = xG_favored + xG_underdog            // 范围约 1.8 ~ 3.2

// 动机修正
if step3.MAF > 0.15 AND step3.MDI < 0:
    xG_favored  *= 0.85   // 强队不全力，进球减少
    xG_underdog *= 1.10   // 弱队拼命，进球略增
```

#### 5.5.2 常见比分概率分布

使用 Poisson 分布近似，λ 分别取 xG_favored 和 xG_underdog：

```
1. 计算比分矩阵 P(i,j) = Poisson(xG_favored, i) × Poisson(xG_underdog, j)
   取 i, j ∈ [0, 5]（覆盖99%+的真实比分）

2. 按结果类型分组：
   favored_win_scores = 所有 i > j 的比分
   draw_scores        = 所有 i == j 的比分
   upset_scores       = 所有 i < j 的比分

3. 按行归一化到 STEP 5 的三分概率：
   favored_win_scores 中每个比分概率 × (final_favored_win / sum(favored_win_scores))
   draw_scores 中每个比分概率        × (final_draw / sum(draw_scores))
   upset_scores 中每个比分概率       × (final_upset / sum(upset_scores))

4. 取概率最高的 Top 5 比分输出
```

#### 5.5.3 总进球数区间概率

```
"0-1_goals": Poisson(xG_total, k=0) + Poisson(xG_total, k=1)
"2-3_goals": Poisson(xG_total, k=2) + Poisson(xG_total, k=3)
"4+_goals":  1 - sum(above)
```

#### 5.5.4 双方进球概率 (BTTS)

```
P(BTTS=YES) = (1 - Poisson(xG_favored, 0)) × (1 - Poisson(xG_underdog, 0))
P(BTTS=NO)  = 1 - P(BTTS=YES)
```

---

### STEP 6: 淘汰赛路径博弈分析 (Knockout Path Analysis)

**目标**：基于上方"淘汰赛对阵参考数据"，评估小组排名偏好对淘汰赛对阵的影响，反馈修正 STEP 3。

**执行指令**：

```
1. 根据当前积分格局，推算本队可能的小组最终排名（第1/第2/第3）

2. 查"半区分布速查表"，确定本组第1名和第2名分别进入哪个半区

3. 评估各排名对应的 R32 对手：
   a. 若排第1 → 查对阵表找到本组第1对应的 R32 比赛，识别对手类型
   b. 若排第2 → 查对阵表找到本组第2对应的 R32 比赛，识别对手类型
   c. 若排第3 → 参照"第三名候选来源约束表"分析（仅在可能出线时）

4. 若 tournament_config.knockout_bracket_snapshot 已注入，使用已确定球队进行精确评估；
   否则基于其他组出线形势做概率性预估。

5. 比较两条路径难度：
   path_diff_as_1st = 第1名路径上潜在对手综合实力
   path_diff_as_2nd = 第2名路径上潜在对手综合实力

6. 路径偏好判定：
   if path_diff_as_2nd < path_diff_as_1st * 0.8:
       knockout_path_bias = -0.05 ~ -0.10（倾向第2名，不想拿第1）
   elif path_diff_as_1st < path_diff_as_2nd * 0.8:
       knockout_path_bias = +0.05 ~ +0.10（倾向第1名）
   else:
       knockout_path_bias = 0.0（无显著差异）

7. 将 knockout_path_bias 反馈给 STEP 3 的 urgency 计算
```

**输出**：`{ step: 6, path_analysis: { as_1st_match, as_2nd_match, as_1st_opponent_estimate, as_2nd_opponent_estimate, path_preference: "1ST_PREFERRED|2ND_PREFERRED|NEUTRAL", knockout_path_bias, confidence } }`

---

## 最终输出规范 (Output Schema)

```json
{
  "match_id": "string",
  "group": "string",
  "round": "integer",
  "prediction": {
    "result": "favored_win | draw | upset",
    "confidence": "HIGH | MEDIUM | LOW",
    "probabilities": {
      "favored_win": "float 0.0-1.0",
      "draw": "float 0.0-1.0",
      "upset": "float 0.0-1.0"
    },
    "favored_team": "string",
    "underdog_team": "string | null",
    "score_probabilities": {
      "top_scores": [
        {"score": "string — 如 '2-1'", "probability": "float", "result_type": "favored_win|draw|upset"}
      ],
      "expected_goals": {
        "favored_team_xG": "float",
        "underdog_team_xG": "float",
        "total_xG": "float"
      },
      "total_goals_distribution": {
        "0-1_goals": "float",
        "2-3_goals": "float",
        "4+_goals": "float"
      },
      "both_teams_to_score": "float 0.0-1.0"
    }
  },
  "upset_alert": {
    "triggered": "boolean",
    "level": "STRONG | MODERATE | NONE",
    "reasoning": "string"
  },
  "strategic_motivation_summary": {
    "assessed": "boolean",
    "key_finding": "string — 核心发现",
    "maf": "float — 动机调整幅度",
    "mdi_direction": "string — 动机偏向哪方"
  },
  "analysis_trace": {
    "step1_base": "object",
    "step2_pattern": "object",
    "step3_motivation": "object",
    "step4_third_place": "object",
    "step6_path": "object | null"
  },
  "group_impact": {
    "home_projected_group_finish": "1st | 2nd | 3rd | 4th",
    "away_projected_group_finish": "1st | 2nd | 3rd | 4th",
    "home_advance_probability": "float 0.0-1.0",
    "away_advance_probability": "float 0.0-1.0"
  }
}
```

---

## 关键分析因子权重

| 因子 | 权重 | 来源 |
|------|------|------|
| FIFA排名差（实力基线） | 40% | 2022全部48场小组赛 |
| 策略性动机 | 25% | 2022第3轮放水案例 + 2026赛制推导 |
| 爆冷模式匹配 | 15% | 2022年11场小组赛爆冷 |
| 第3名出线博弈 | 10% | 2026赛制独有 |
| 淘汰赛路径偏好 | 10% | 2026赛制新增维度 |

---

## 使用说明

1. **逐场执行**：对每场小组赛独立运行本 skill，按 STEP 0→6 顺序执行
2. **STEP 0 优先**：必须在推理前执行实时数据搜索，获取的 `realtime_data` 贯穿 STEP 2/3/5
3. **信息累积**：每场比赛执行完后，将结果更新到 `group_context.completed_matches` 中
4. **跨组信息**：第三轮需利用 `tournament_context` 进行第3名出线概率估算
5. **独立可用**：本文件完全自包含（含对阵表），可直接交给具备 web search 能力的大模型使用
6. **输出消费**：`prediction` 和 `group_impact` 输出将被 `knockout_stage_predict` 和 `championship_predict` 直接消费

---

*基于2022年卡塔尔世界杯64场比赛数据设计，适配2026年美加墨世界杯赛制*
*版本2.1 — 新增 STEP 0 实时数据自主获取、淘汰赛对阵表内嵌、比分概率推导（STEP 5.5）、修复 STEP 5 合成逻辑*
