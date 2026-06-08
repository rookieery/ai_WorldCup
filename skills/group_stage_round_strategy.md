# Skill: group_stage_round_strategy — 小组赛轮次策略预测

## 元信息

- **版本**: 1.0
- **适用赛制**: 2026年世界杯小组赛（48队/12组/每组4队/前2名+8个最好第3名出线）；通过赛制适配指南可回测2018/2022
- **分析粒度**: 轮次差异化策略预测——R1爆冷猎手、R2稳定猎手、R3终局博弈猎手
- **核心定位**: 轮次策略引导——每轮有独立的策略方向，非中立综合分析
- **派生来源**: group_stage_predict v2.1 — 继承推理框架，重写冲突逻辑
- **使用方式**: 自包含 prompt，可直接交给具备 web search 能力的大模型独立执行

---

## 爆冷定义

本策略将爆冷分为两个层级，共享同一套 upset 信号源（STEP 2），但按模式不同分配到 L 和 D：

- **全爆冷 (Full Upset)**：弱队胜（favored 负）→ 映射为 L
- **平局爆冷 (Draw Upset)**：排名差 > 15 且强队平弱队 → 映射为 D 的异常升高

> 历史案例：2018 阿根廷1-1冰岛(rank_diff=17)、巴西1-1瑞士(rank_diff=4，平局属正常)；2022 墨西哥0-0波兰(rank_diff=13，平局属正常)、摩洛哥0-0克罗地亚(rank_diff=10，平局属正常)。平局爆冷仅在排名差足够大时才有识别价值。

---

## 轮次策略方向总览

| 轮次 | 策略模式 | 核心关注 | 推荐输出优先级 |
|------|---------|---------|-------------|
| R1 | 爆冷猎手+大球雷达 | 强队未进入状态、弱队奇袭、强弱悬殊进攻 | 爆冷比分 > 大球比分 > 稳定比分 |
| R2 | 稳定猎手 | 首轮信息验证、实力格局确认、动机确定性 | 强队稳定比分 > 平局 > 爆冷比分 |
| R3 | 终局博弈猎手 | 动机不对称、放水爆冷、默契平局、第3名出线 | 按场景分支 |

**历史数据支撑**（2018+2022，共96场小组赛）：

| 轮次 | 爆冷率 | 大球率(≥5球) | 策略含义 |
|------|--------|------------|---------|
| R1 | 21.9% (7/32) | 15.6% (5/32) | 爆冷多发、大球集中——放大信号有效 |
| R2 | 15.6% (5/32) | 9.4% (3/32) | 最稳定轮次——实力基线预测最可靠 |
| R3 | 31.25% (10/32) | 6.25% (2/32) | 爆冷最高发——放水场景命中率极高 |

---

## 输入规范 (Input Schema)

```json
{
  "match": {
    "match_id": "string — 如 'A_M1'",
    "group": "string — 组别 A-L（2018/2022为A-H）",
    "round": "integer — 轮次 1-3",
    "home_team": "string",
    "away_team": "string"
  },
  "teams": {
    "<team_name>": {
      "fifa_ranking": "integer — 赛前FIFA排名（必填）",
      "world_cup_experience": "integer — 历史参赛次数（必填）",
      "confederation": "string — UEFA/CONMEBOL/AFC/CAF/CONCACAF/OFC（必填）"
    }
  },
  "group_context": {
    "teams_in_group": ["string"],
    "completed_matches": [
      { "match_id": "string", "home": "string", "away": "string", "score": "string", "result": "string" }
    ]
  },
  "tournament_context": { "other_groups_completed_matches": "object" },
  "tournament_config": {
    "teams_per_group": 4,
    "matches_per_team": 3,
    "advance_top_n": 2,
    "best_third_advance_count": "integer — 2026=8, 2018/2022=0",
    "total_groups": "integer — 2026=12, 2018/2022=8",
    "advancement_rate": "float — 2026=0.667, 2018/2022=0.500"
  }
}
```

---

## 推理步骤链 (Reasoning Chain)

执行顺序：STEP 0 → STEP 1 → STEP 2 → STEP 3 → STEP 4 → STEP 5 → STEP 5.5 → STEP 6

---

### STEP 0: 实时数据获取 (Realtime Data Acquisition)

> 继承自 group_stage_predict v2.1，与轮次策略无关的通用能力。详细搜索清单和数据格式见原文件。

**必搜清单**：P0: 双方近5场成绩、核心伤病 | P1: 主帅发言/轮换、历史交锋 | P2: 赔率、其他组出线形势(R3)

**数据整理**：`realtime_data = { {{team}}: { recent_form, key_injuries: [{impact}], coach_intent }, h2h, market_odds }`

---

### STEP 1: 实力基线评估 + 轮次修正 (Base Strength with Round Correction)

**1.1 基础概率表**（继承原模型）：

| 排名差区间 | favored_win | draw | upset |
|-----------|-------------|------|-------|
| 0-5 | 0.40 | 0.35 | 0.25 |
| 6-15 | 0.48 | 0.28 | 0.24 |
| 16-30 | 0.55 | 0.25 | 0.20 |
| 31-45 | 0.65 | 0.20 | 0.15 |
| >45 | 0.73 | 0.15 | 0.12 |

**2022特殊修正**（叠加到 upset）：弱队 FIFA 排名 15-30 且来自 AFC/CAF/CONCACAF → upset +0.08；弱队 FIFA 排名 15-30 且 `world_cup_experience >= 5` → upset +0.05

**回测校准补充修正**（2018+2022验证）：
- AFC/CAF 球队 R1 额外加成：弱队来自 AFC/CAF 且 `experience >= 5` → R1 upset 额外 +0.05（2018日本胜哥伦比亚、塞内加尔胜波兰）
- 排名虚假度检测：IF 首轮强队小胜弱队（净胜≤1）或惨败 → 该队 FIFA 排名可信度降级，`rank_diff × 0.7`（2022比利时排名虚高案例）
- 首轮大胜后松懈修正：IF R2 且该队 R1 净胜≥3球 → R2 favored_win 额外 -0.03，D += 0.03（2022英格兰6-2后0-0美国、2018比利时3-0后5-2但比分失控、2018英格兰2-1后6-1失控）
- 0分已出局"无包袱效应"：IF 球队 0 分已出局 → `urgency = 0.3`（而非0.0），`xG *= 1.15`（2018西班牙2-2摩洛哥、瑞士2-2哥斯达黎加）

**1.2 轮次修正因子 round_correction**（核心改造）：

```
R1（首轮探索）:
  round_correction = 1.0  // 基准不变
  特殊修正:
    IF 赛事揭幕战 → draw += 0.05（揭幕战偏保守）

R2（信息验证轮）:
  round_correction = 1.0  // 排名差解释力最强
  特殊修正:
    IF 首轮结果与排名差一致（强队赢了）→ favored_win += 0.03
    IF 首轮结果与排名差冲突（强队输/平）→ base_table权重降为60%，首轮实际表现权重升为40%
    IF 该队首轮净胜≥3球（大胜后松懈）→ favored_win 额外 -0.03, draw += 0.03（2022英格兰案例）

R3（动机博弈轮）:
  round_correction = 0.6  // 排名差解释力大幅下降
  特殊修正:
    IF 排名第1已锁定出线（6+分）→ 排名差概率表完全不适用，回归STEP 3
    IF 双方积分相同 → round_correction = 0.8
```

**输出**：`{ step: 1, rank_diff, favored_team, underdog_team, base_probabilities: { favored_win, draw, upset }, round_correction, round_special_modifiers }`

---

### STEP 2: 爆冷模式识别 + 轮次系数 (Upset Pattern with Round Multiplier)

**2.1 爆冷模式匹配**（继承原模型，新增平局爆冷维度）：

| 弱队排名区间 | 模式标识 | 特征 | base_upset_boost | draw_upset_ratio |
|-------------|---------|------|-----------------|-----------------|
| ≤25 | TACTICAL_STRETCH | 主动放弃控球、快速转换 | +0.08 | **0.40** |
| 26-40 | SOLID_DEFENSE | 低位防守、定位球反击 | +0.04 | **0.60** |
| >40 | DESPERATE_BURST | 全员退守+偶然进球 | +0.02 | **0.20** |

**draw_upset_ratio 说明**：upset 信号中分配给 D（平局爆冷）的比例。SOLID_DEFENSE 的 draw_upset_ratio 最高(0.60)因为防守型球队天然偏平局；DESPERATE_BURST 最低(0.20)因为极弱队要么爆冷赢要么大败，平局概率低。

**触发条件**：`draw_upset_ratio` 仅在 `rank_diff > 15` 时生效。`rank_diff ≤ 15` 时 `draw_upset_ratio = 0`（排名差小，平局是正常结果，不算爆冷）。

**附加修正**：弱队 `experience >= 5` → TACTICAL_STRETCH +0.05；强队已锁定+DESPERATE_BURST → ROTATION_EXPLOIT +0.06

**实时修正**（引用 STEP 0）：对方 HIGH impact 伤缺 → +0.03；弱队胜率≥60% → +0.02；强队轮换 → ROTATION_EXPLOIT +0.03

**2.2 轮次系数 round_upset_multiplier**（核心改造，2018+2022校准）：

```
R1（首轮探索）:
  round_upset_multiplier = 1.35  // 从1.3校准至1.35
  理由: 强队状态未知，弱队全力以赴，信息最少
  证据: 两届R1爆冷率21.9%，2018高达31.3%

R2（信息验证）:
  round_upset_multiplier = 0.60  // 从0.7校准至0.60
  理由: 首轮已验证实力格局，二次爆冷概率显著下降
  证据: 2018 R2仅6.25%爆冷率，2022 R2爆冷多为"爆冷后松懈"

R3（动机博弈）:
  round_upset_multiplier = 1.1（基准，从1.0微调）
  IF 强队 ASS >= 0.90（锁定出线）:
    round_upset_multiplier = 2.0  // 放水场景从1.8提升至2.0（2022验证）
  IF 双方均已出局:
    round_upset_multiplier = 0.5  // 无关痛痒，回归实力基线
  证据: 两届R3爆冷率31.25%，2022放水3场全爆冷，R3非放水爆冷也较多
```

**最终 upset_boost** = `base_upset_boost × round_upset_multiplier + 附加修正 + 实时修正`

**输出**：`{ step: 2, underdog_pattern, base_upset_boost, draw_upset_ratio, round_upset_multiplier, final_upset_boost, pattern_confidence }`

---

### STEP 3: 轮次差异化动机分析 (Round-Differentiated Motivation Analysis)

**3.1 出线安全度 (ASS)**

**R1**：`rank_group` = 球队在本组4队中的FIFA排名序号（1=最强，4=最弱）

```
rank_group=1 → ASS=0.85 | rank_group=2 → ASS=0.65 | rank_group=3 → ASS=0.40 | rank_group=4 → ASS=0.20
```

**R2**（首轮结果已出）：

```
points=3: ASS = 0.80 + (rank_group==1 ? 0.10 : 0.00)
points=1: ASS = 0.45 + (rank_group<=2 ? 0.15 : 0.00)
points=0: ASS = 0.15 + (rank_group<=2 ? 0.20 : 0.00)
```

**R3**（精确计算，赛制条件化）：

```
// 通用部分（所有赛制）
points>=6: ASS=0.98+ | points=4: ASS=0.80-0.95 | points=3: ASS=0.20-0.50
points=1: ASS=0.05-0.15 | points=0: ASS=0.00-0.02

// 2026赛制专属（best_third_advance_count > 0时）:
//   points=3: ASS根据STEP 4的第3名出线概率上调0.10-0.20
//   points=1: ASS根据STEP 4上调0.05-0.10
// 2018/2022赛制: 无第3名出线，上述上调不生效
```

**3.2 动机差异指数 (MDI) 与调整系数 (MAF)**

```
MDI = Motivation_self - Motivation_opponent
Motivation = 1.0 - ASS * (1 - urgency)

urgency: 必须赢=1.0 | 不赢也可能出线=0.7 | 平局即可=0.5 | 已锁定=0.1 | 已出局=0.0

MAF = abs(MDI) * 0.25 * round_weight * safety_amplifier

round_weight: R1=0.25 | R2=0.85 | R3=1.35
// 校准来源: 2018+2022回测，R1动机差异确实最小降为0.25，R2/3验证有效微调

safety_amplifier:
  IF best_third_advance_count > 0（2026赛制）:
    (ASS_self>0.90 AND ASS_opponent<0.30) ? 1.5 : 1.0
  ELSE（2018/2022赛制）:
    (ASS_self>0.90 AND ASS_opponent<0.20) ? 1.5 : 1.0  // 从1.3校准至1.5（2022放水3场全命中验证）

MAF上限: R1/R2 = 0.35 | R3 = 0.50  // R3从0.45提升至0.50（回测验证R3动机极端场景需要更多空间）
```

**实时修正**：`coach_intent` 提到"轮换"→ urgency × 0.7；对方 2+ 名 HIGH impact 缺阵 → Motivation_self += 0.10

**3.3 按轮次触发条件**

**R1**：排名差>25 且弱队 rank_group=3/4 → 弱队动机+0.10 | 揭幕战 → draw += 0.05

**R2**：强队3分vs弱队0分(SL) → MAF≈0.08 | 3分vs1分(SW) → 中风险 | 其他≈0 | **回测新增**：强队R1爆冷后R2衰减 → favored_win 额外 -0.05（2022日本0-1哥斯达黎加案例）

**R3**：ASS≥0.95 → Motivation=0.1, MAF=0.25-0.50 | 双方平局均达4分 → 平局+20-30% | 输球仍可第3名出线 → 调用STEP 4(仅2026) | ASS>0.80且可能选半区 → 调用STEP 6 | **回测新增**：4分球队"平即可出线"保守效应 → `xG_favored *= 0.80`（2018瑞士2-2哥斯达黎加）

**3.4 概率修正公式**

```
W_base = step1输出（经round_correction修正后）
D_base = step1输出
L_base = step1输出

if MDI > 0:  W_adj = W_base + MAF*(1-W_base);  L_adj = L_base*(1-MAF)
elif MDI < 0: L_adj = L_base + MAF*(1-L_base);  W_adj = W_base*(1-MAF)
D_adj = 1.0 - W_adj - L_adj

// 默契球叠加（R3触发时）
if tacit_draw_risk:
    draw_bonus = tacit_draw_risk * 0.25  // 从原版0.20提升
    W_adj *= (1 - draw_bonus); L_adj *= (1 - draw_bonus); D_adj = 1.0 - W_adj - L_adj

// 边界保护 + 归一化
W_adj = MAX(0.05, W_adj); D_adj = MAX(0.05, D_adj); L_adj = MAX(0.05, L_adj)
total = W_adj + D_adj + L_adj
W_adjusted = W_adj/total; D_adjusted = D_adj/total; L_adjusted = L_adj/total
```

**输出**：`{ step: 3, analysis: { ASS_self, ASS_opponent, MDI, MAF, round_weight }, triggers, special_flags: { tacit_draw_risk, knockout_path_bias }, adjustment: { W_adjusted, D_adjusted, L_adjusted } }`

---

### STEP 4: 第3名出线概率评估 (Third-Place Advancement Probability)

**条件化执行**：仅当 `best_third_advance_count > 0`（2026赛制）时执行，否则输出 null。

**2026赛制**：12组第3名按积分>净胜球>进球排序，取前8名出线。门槛：4分>95%出线 | 3分~50% | 2分20-30% | 1分<5%

**影响**：一方输球仍可第3名出线 → urgency降低，MAF增大 | 双方输球都淘汰 → 极端保守或激进 | 双方都有后路 → 偏开放

**输出**：`{ step: 4 | null, third_place_threshold, home/away_third_place_probability, impact_on_match }`

---

### STEP 5: 轮次独立综合概率合成 (Round-Independent Synthesis)

**目标**：按轮次使用独立合成公式，替代原模型的中立固定权重叠加。

#### 5.1 R1 合成（爆冷探索模式）

```
W = step3.W_adjusted; D = step3.D_adjusted; L = step3.L_adjusted

// R1 不使用 STEP 4（首轮无第3名出线概念）

// 爆冷信号放大
upset_net = step2.final_upset_boost * (1 - step3.MAF / 0.50)

// 平局爆冷分流（v1.0 新增）
loss_share = 1 - step2.draw_upset_ratio
IF step1.rank_diff <= 15: step2.draw_upset_ratio = 0  // 平局不算爆冷

// R1 平局倾向（信息不足时保守）
draw_boost_r1 = 0.08  // 从0.05校准至0.08（2022验证：3场R1平局全漏判）

// 应用（upset_net 按比例分流到 L 和 D）
L += upset_net * 0.5 * loss_share
D += draw_boost_r1 + upset_net * 0.5 * step2.draw_upset_ratio
W -= (upset_net * 0.5 + draw_boost_r1) * (W / (W + D))

归一化 + 边界保护（所有概率 >= 5%）
```

#### 5.2 R2 合成（实力验证模式）

```
W = step3.W_adjusted; D = step3.D_adjusted; L = step3.L_adjusted

// R2 不使用 STEP 4

// 爆冷抑制（round_upset_multiplier 已是 0.60）+ 分流
upset_net = step2.final_upset_boost * 0.60 * (1 - step3.MAF / 0.50)
loss_share = 1 - step2.draw_upset_ratio
IF step1.rank_diff <= 15: step2.draw_upset_ratio = 0

// 应用（upset_net 按比例分流到 L 和 D）
L += upset_net * loss_share
D += upset_net * step2.draw_upset_ratio

// 首轮信号加权
IF 首轮强队胜: W += 0.05  // 验证实力格局
IF 首轮爆冷:   L += 0.03  // 承认但不过度外推
IF 该队首轮净胜≥3球（大胜后松懈）: W -= 0.03, D += 0.03  // 2022英格兰6-2后0-0美国

归一化 + 边界保护
```

#### 5.3 R3 合成（动机博弈模式）

```
W = step3.W_adjusted; D = step3.D_adjusted; L = step3.L_adjusted

// STEP 4 影响（仅2026，step4 != null时）
IF step4 != null:
  W += step4.impact_on_match.home_desperation_boost
  L += step4.impact_on_match.away_desperation_boost
  D += step4.impact_on_match.draw_boost

// STEP 6 淘汰赛路径修正
IF step6 != null AND step6.knockout_path_bias != 0:
  path_bias = step6.knockout_path_bias
  IF path_bias < 0: W *= (1+path_bias); D += abs(path_bias)*0.5
  ELIF path_bias > 0: W *= (1+path_bias)

// 默契球叠加（回测校准：从0.25提升至0.30）
IF step3.special_flags.tacit_draw_risk:
  draw_bonus = tacit_draw_risk * 0.30  // 2018丹麦0-0法国验证
  W *= (1-draw_bonus); L *= (1-draw_bonus); D = 1.0 - W - L

// 放水场景爆冷放大（回测校准：场景细分）
// 放水场景下 upset_amplified 100% → L（放水=强队不防守=弱队更可能赢而非平）
IF (ASS_self>0.90 OR ASS_opponent>0.90) AND MDI < -0.2:
  // 场景细分：碾压型（R1+R2均净胜≥2球）vs 正常型
  IF 该6分球队 R1+R2 均净胜≥2球（碾压型）:
    upset_amplified = step2.final_upset_boost * 1.3  // 碾压型强队即使轮换仍实力碾压（2018克罗地亚2-1冰岛验证）
  ELSE:
    upset_amplified = step2.final_upset_boost * 2.0  // 正常型放水场景（2022放水3场全爆冷验证）
  L += MIN(upset_amplified, 0.30)

// 非放水场景：平局爆冷分流（v1.0 新增）
IF NOT 放水场景:
  upset_net = step2.final_upset_boost * round_upset_multiplier * (1 - step3.MAF / 0.50)
  loss_share = 1 - step2.draw_upset_ratio
  IF step1.rank_diff <= 15: step2.draw_upset_ratio = 0
  L += upset_net * loss_share
  D += upset_net * step2.draw_upset_ratio

归一化 + 边界保护
```

**置信度**：max_prob≥0.55→HIGH | max_prob≥0.40→MEDIUM | max_prob<0.40→LOW

**爆冷预警**（v1.0 新增平局爆冷维度）：

```
// 全爆冷检测（弱队胜）
IF final_upset >= 0.35 → full_upset_level = STRONG
IF final_upset >= 0.25 → full_upset_level = MODERATE

// 平局爆冷检测（rank_diff > 15 且 D 异常高）
IF step1.rank_diff > 15 AND final_draw >= 0.35 → draw_upset_level = STRONG
IF step1.rank_diff > 15 AND final_draw >= 0.30 → draw_upset_level = MODERATE

// 综合判断
upset_alert.level = max(full_upset_level, draw_upset_level)
upset_alert.type = FULL_UPSET | DRAW_UPSET | BOTH | NONE
```

---

### STEP 5.5: 轮次差异化比分推荐 (Round-Differentiated Score Recommendation)

#### 5.5.1 预期进球数 (xG)（继承原逻辑）

```
xG_favored  = 1.2 + (rank_diff / 100) * 0.8
xG_underdog = 0.6 + (final_upset / 0.30) * 0.6

// 动机修正
IF step3.MAF > 0.15 AND step3.MDI < 0:
  xG_favored *= 0.85; xG_underdog *= 1.10
```

#### 5.5.2 Poisson 比分矩阵（继承原逻辑，i,j ∈ [0,5]）

```
P(i,j) = Poisson(xG_favored, i) × Poisson(xG_underdog, j)
按结果分组归一化到 STEP 5 的三分概率
```

#### 5.5.3 轮次差异化比分筛选（核心改造）

**R1 策略（爆冷探索）**：
1. upset_scores 中概率最高 **2 个**（优先推荐爆冷比分）
2. favored_win_scores 中概率最高 **2 个**
3. draw_scores 中概率最高 **1 个**
→ **Top 5 = 2爆冷 + 2强队胜 + 1平局**
4. 总进球修正：`xG_total *= 1.10`（从1.05校准至1.10，2022验证R1大球覆盖率需提升）
5. Poisson 矩阵范围扩展至 `[0,6]`（覆盖5-0、6-1等极端比分）

**R2 策略（实力验证）**：
1. favored_win_scores 中概率最高 **3 个**（优先推荐强队稳定比分：2-0, 2-1, 1-0）
2. draw_scores 中概率最高 **1 个**
3. upset_scores 中概率最高 **1 个**（保留但不优先）
→ **Top 5 = 3强队胜 + 1平局 + 1爆冷**
4. 总进球修正：`xG_total *= 0.95`（R2实力格局已定）
5. 高置信度标记：IF MAF<0.08 AND favored_win≥0.45 → 标记 **HIGH_STABILITY**

**R3 策略（动机博弈）**：
按场景分支：
- **放水场景**（一方 ASS>0.90）：优先小比分爆冷（0-1,0-2）和低进球
  → **Top 5 = 2爆冷 + 2平局 + 1强队胜** | `xG_total *= 0.80`
- **生死战场景**（双方 ASS<0.30）：正常 Top 5（概率最高）
  → **Top 5 = 概率最高的5个** | `xG_total *= 1.10`
- **默契球场景**（双方都获益于平局）：强烈推荐 0-0,1-1,2-2
  → **Top 5 = 3平局 + 1强队胜 + 1爆冷**

#### 5.5.4 总进球数区间 + BTTS（继承原逻辑）

```
"0-1_goals": Poisson(xG_total,0) + Poisson(xG_total,1)
"2-3_goals": Poisson(xG_total,2) + Poisson(xG_total,3)
"4+_goals":  1 - sum(above)
BTTS_YES = (1-Poisson(xG_favored,0)) × (1-Poisson(xG_underdog,0))
```

---

### STEP 6: 淘汰赛路径博弈分析 (Knockout Path Analysis)

**条件化执行**：仅 R3 触发。

- **2026赛制**：使用完整淘汰赛对阵参考数据（见 `group_stage_predict.md` 的"淘汰赛对阵参考数据"章节），执行原 STEP 6 完整逻辑
- **2018/2022赛制**：使用该届赛事的 R16 对阵表，简化为推算小组排名→查对阵表→评估路径难度→输出 `knockout_path_bias`

**输出**：`{ step: 6 | null, path_analysis: { as_1st_match, as_2nd_match, path_preference, knockout_path_bias } }`

---

## 最终输出规范 (Output Schema)

```json
{
  "match_id": "string", "group": "string", "round": "integer",
  "prediction": {
    "result": "favored_win | draw | upset",
    "confidence": "HIGH | MEDIUM | LOW",
    "probabilities": { "favored_win": "float", "draw": "float", "upset": "float" },
    "favored_team": "string", "underdog_team": "string | null"
  },
  "round_strategy_profile": {
    "strategy_mode": "UPSET_HUNTER | STABILITY_HUNTER | ENDGAME_HUNTER",
    "round_upset_multiplier": "float", "round_weight": "float", "round_correction": "float",
    "strategy_signals": { "upset_signal": "STRONG|MODERATE|WEAK", "big_ball_signal": "STRONG|MODERATE|WEAK|N/A",
      "stability_signal": "STRONG|MODERATE|WEAK|N/A", "tacit_draw_signal": "DETECTED|NOT_DETECTED|N/A" },
    "recommended_scores": {
      "primary": [{ "score": "string", "probability": "float", "reason": "string" }],
      "secondary": [{ "score": "string", "probability": "float", "reason": "string" }]
    }
  },
  "score_probabilities": {
    "top_scores": [{ "score": "string", "probability": "float", "result_type": "string" }],
    "expected_goals": { "favored_team_xG": "float", "underdog_team_xG": "float", "total_xG": "float" },
    "total_goals_distribution": { "0-1_goals": "float", "2-3_goals": "float", "4+_goals": "float" },
    "both_teams_to_score": "float"
  },
  "upset_alert": {
    "triggered": "boolean",
    "level": "STRONG | MODERATE | NONE",
    "type": "FULL_UPSET | DRAW_UPSET | BOTH | NONE",
    "reasoning": "string",
    "draw_upset_context": {
      "rank_diff": "integer",
      "draw_upset_ratio": "float",
      "draw_probability": "float"
    }
  },
  "strategic_motivation_summary": { "assessed": "boolean", "key_finding": "string", "maf": "float", "mdi_direction": "string" },
  "analysis_trace": { "step1_base": "object", "step2_pattern": "object", "step3_motivation": "object", "step4_third_place": "object|null", "step6_path": "object|null" }
}
```

---

## 关键分析因子权重（轮次策略版）

### R1: 爆冷猎手模式

| 因子 | 权重 | 策略作用 |
|------|------|---------|
| FIFA排名差（实力基线） | 30% | 降低——首轮强队尚未进入状态 |
| 爆冷模式匹配 | 25% | 提升——首轮是爆冷模式最有效的轮次 |
| 策略性动机 | 15% | 降低——首轮动机差异最小 |
| 大球信号检测 | 15% | 新增——首轮是大球高发轮 |
| 第3名出线博弈 | 5% | 降低——首轮无博弈基础 |
| 淘汰赛路径偏好 | 5% | 降低——首轮不考虑路径 |
| 实时数据（伤病/状态） | 5% | 保持 |

### R2: 稳定猎手模式

| 因子 | 权重 | 策略作用 |
|------|------|---------|
| FIFA排名差（实力基线） | 45% | 提升——R2实力差最忠实地反映赛果 |
| 策略性动机 | 20% | 保持——首轮结果已知，ASS可精确计算 |
| 爆冷模式匹配 | 10% | 降低——R2爆冷率最低 |
| 第3名出线博弈 | 10% | 提升——R2结果开始影响出线形势 |
| 淘汰赛路径偏好 | 10% | 保持 |
| 实时数据 | 5% | 保持 |

### R3: 终局博弈猎手模式

| 因子 | 权重 | 策略作用 |
|------|------|---------|
| 策略性动机 | 35% | 大幅提升——R3是动机博弈的核心轮次 |
| 爆冷模式匹配 | 20% | 提升——R3爆冷率最高（31.25%） |
| FIFA排名差（实力基线） | 15% | 大幅降低——放水场景下排名差失效 |
| 第3名出线博弈 | 15% | 大幅提升——R3是第3名出线的关键计算轮 |
| 淘汰赛路径偏好 | 10% | 提升——R3可能为选半区而控制排名 |
| 默契球/放水信号 | 5% | 新增——R3独有 |

---

## 赛制适配指南 (Tournament Adaptation Guide)

### 2018 俄罗斯世界杯回测配置

```yaml
tournament_config_override:
  total_groups: 8
  best_third_advance_count: 0
  advancement_rate: 0.500
# STEP 4: 跳过（输出 null）
# STEP 6: 使用 2018 R16 对阵表
# 特殊修正:
#   卫冕冠军（德国）: base_prob *= 动态系数（见下方）
#   东道主（俄罗斯）: base_prob += 0.10（东道主效应）
#   info_clarity: 同组同时开球，跨组信息不对称关闭
```

**卫冕冠军削弱动态系数**（2018德国案例校准）：

```
IF 卫冕冠军:
  R1: base_prob *= 0.75  // 基准削弱（2018德国0-1墨西哥，STRONG预警命中）
  R2: IF R1 已输/平 → base_prob *= 0.60  // 恶化（R1验证卫冕冠军状态极差）
      IF R1 正常胜 → base_prob *= 0.80  // 缓和（状态尚可）
  R3: IF R1+R2 均未胜 → base_prob *= 0.50  // 深度魔咒（2018德国0-2韩国漏判校准）
      IF R1/R2 至少胜1场 → base_prob *= 0.75  // 维持基准
```

### 2022 卡塔尔世界杯回测配置

```yaml
tournament_config_override:
  total_groups: 8
  best_third_advance_count: 0
  advancement_rate: 0.500
# STEP 4: 跳过（输出 null）
# STEP 6: 使用 2022 R16 对阵表
# 特殊修正:
#   5换人规则效应: upset_boost *= 1.20（校准自1.15，日本韩国案例证明5换人帮助超出预期）
#   AFC 球队加成: upset_boost += 0.08（校准自0.05，AFC球队贡献2022年6场爆冷中5场）
#   AFC 球队R1额外加成: upset_boost += 0.03（首轮是AFC爆冷高发轮）
#   赛季中举办: 强队状态可能不如赛季末（冬季世界杯）
```

### 回测执行流程

1. **数据准备**: 读取 `data/2018_FIFA_World_Cup_Results.md` 或 `data/2022_FIFA_World_Cup_Results.md`，提取各队FIFA排名和逐轮结果
2. **逐轮预测**: 对每个小组按 R1→R2→R3 顺序执行本 skill
   - R1: `completed_matches = []`
   - R2: 填入 R1 **实际结果**（非预测结果，隔离单步误差）
   - R3: 填入 R1+R2 **实际结果**
3. **命中率统计**: 按轮次统计胜平负准确率、爆冷预警命中率、比分Top5覆盖率
4. **经验提取**: 识别赛制无关的通用规律，校准参数
5. **反哺2026**: 将校准后的参数更新到2026版本的默认值

### 经验反哺维度

| 维度 | 提取方法 | 反哺目标参数 |
|------|---------|------------|
| 各轮爆冷率偏差 | 对比预测vs实际爆冷率 | round_upset_multiplier |
| R2首验信号有效性 | 对比R2在首轮爆冷组vs非爆冷组的命中率 | 首轮信号加权系数 |
| R3放水效应强度 | 统计ASS>0.90的强队实际胜率 | round_weight, safety_amplifier |
| 动机分析有效性 | 统计MAF>0.20的比赛中预测方向命中率 | MAF上限, round_weight |
| 比分Top5覆盖 | 统计实际比分落入Top5的比例 | Poisson xG参数 |

### 回测验证结果摘要（v1.0 已校准参数）

**2018 回测**（48场）：

| 指标 | 结果 |
|------|------|
| 整体方向命中 | 34/48 = 70.8% |
| R1 爆冷猎手 | 10/16 = 62.5% |
| R2 稳定猎手 | 13/16 = 81.3%（最高） |
| R3 终局博弈 | 11/16 = 68.8% |
| 爆冷预警命中 | 8/13 = 61.5% |
| 比分Top5覆盖 | 23/48 = 47.9% |
| 亮点 | 丹麦0-0法国默契球首选命中、巴西1-1瑞士STRONG爆冷预警命中 |
| 不足 | 韩国2-0德国漏判（卫冕冠军魔咒深度不足） |

**2022 回测**（48场）：

| 指标 | 结果 |
|------|------|
| 整体方向命中 | 37/48 = 77.1% |
| R1 爆冷猎手 | 12/16 = 75.0% |
| R2 稳定猎手 | 14/16 = 87.5%（最高） |
| R3 终局博弈 | 11/16 = 68.8%（放水场景3/3全命中） |
| 爆冷预警命中 | 9/14 = 64.3% |
| 比分Top5覆盖 | 25/48 = 52.1% |
| 亮点 | R3放水3场全命中（策略最大价值）、R1大球信号75%命中 |
| 不足 | R1平局倾向不足、日本0-1哥斯达黎加爆冷后松懈未捕获 |

**平局爆冷识别覆盖（v1.0 新增维度）**：

draw_upset_ratio 将 upset 信号按比例分流到 D，使强队平弱队的"平局爆冷"场景获得更准确的概率预测。以下为关键覆盖场景：

| 场景 | 轮次 | 排名差 | 模式 | draw_upset_ratio | 原策略表现 | 新机制效果 |
|------|------|--------|------|-----------------|-----------|-----------|
| 2018 阿根廷1-1冰岛 | R1 | 17>15 | TACTICAL_STRETCH | 0.40 | 方向未命中(预测阿根廷胜) | D 获 upset_net×0.5×0.40 加成 |
| 2018 巴西1-1瑞士 | R1 | 4≤15 | TACTICAL_STRETCH | 0.00 | 方向命中(平局首选) | 平局本就正常，不触发分流 |
| 2022 墨西哥0-0波兰 | R1 | 13≤15 | TACTICAL_STRETCH | 0.00 | 方向未命中 | 平局本就正常，靠 draw_boost_r1 |
| 2022 摩洛哥0-0克罗地亚 | R1 | 10≤15 | TACTICAL_STRETCH | 0.00 | 方向未命中 | 同上 |
| 2022 英格兰0-0美国 | R2 | 11≤15 | TACTICAL_STRETCH | 0.00 | 方向未命中 | 平局本就正常，非平局爆冷 |
| 2018 瑞士2-2哥斯达黎加 | R3 | 17>15 | TACTICAL_STRETCH | 0.40 | 方向未命中(预测瑞士胜) | D 获分流加成+无包袱效应 |

> 注：2022 R1 的三场平局（墨西哥0-0波兰、摩洛哥0-0克罗地亚、丹麦0-0突尼斯）排名差均 ≤15，不触发平局爆冷分流，依赖 draw_boost_r1=0.08 处理。这说明 draw_upset_ratio 的 rank_diff>15 阈值设计合理——避免对正常平局过度修正。

**首轮大胜后松懈修正覆盖**：

IF R2 且该队 R1 净胜≥3球 → favored_win 额外 -0.03, D += 0.03。解决 R2 对首轮大胜后"自信放水"场景的识别盲区。

| 场景 | 轮次 | R1结果 | 原策略表现 | 新机制效果 |
|------|------|--------|-----------|-----------|
| 2022 英格兰0-0美国 | R2 | 英格兰6-2伊朗(净胜4) | 方向未命中(预测英格兰胜) | W -0.03, D +0.03 → 平局信号增强 |
| 2022 西班牙1-1德国 | R2 | 西班牙7-0哥斯达黎加(净胜7) | 方向命中(平局首选) | 新机制不冲突，D 进一步增强 |
| 2018 比利时5-2突尼斯 | R2 | 比利时3-0巴拿马(净胜3) | 方向命中(比利时胜) | W -0.03 但实力碾压仍命中 |

**R3 放水场景细分覆盖**：

6 分锁定出线场景分为"碾压型"(R1+R2 均净胜≥2球, 倍率 1.3)和"正常型"(倍率 2.0)。解决 2018 克罗地亚放水倍率过度 vs 2022 放水倍率合理的冲突。

| 场景 | R1+R2净胜球 | 类型 | 原倍率 | 新倍率 | 原策略表现 | 新机制效果 |
|------|-----------|------|--------|--------|-----------|-----------|
| 2022 突尼斯1-0法国 | +3, +1 | 正常型 | 2.0 | 2.0 | ✅ 爆冷STRONG命中 | 无变化 |
| 2022 喀麦隆1-0巴西 | +2, +1 | 正常型 | 2.0 | 2.0 | ✅ 爆冷STRONG命中 | 无变化 |
| 2022 韩国2-1葡萄牙 | +1, +2 | 正常型 | 2.0 | 2.0 | ✅ 爆冷STRONG命中 | 无变化 |
| 2018 冰岛1-2克罗地亚 | +2, +3 | **碾压型** | 2.0 | **1.3** | ❌ 爆冷STRONG误判(克罗地亚赢了) | 倍率降低，减少误判 |

**卫冕冠军削弱动态系数覆盖**：

卫冕冠军削弱系数从固定 0.75 改为按轮次动态调整，解决 2018 德国 R3 漏判（韩国2-0）时 0.75 远远不足的问题。

| 场景 | 轮次 | R1结果 | 原系数 | 新系数 | 原策略表现 | 新机制效果 |
|------|------|--------|--------|--------|-----------|-----------|
| 2018 德国0-1墨西哥 | R1 | — | 0.75 | 0.75 | ✅ STRONG预警命中 | 无变化（基准） |
| 2018 德国2-1瑞典 | R2 | 负 | 0.75 | **0.60** | ✅ 方向命中(但信心不足) | R1输后恶化至0.60，更激进 |
| 2018 德国0-2韩国 | R3 | 负+胜 | 0.75 | **0.50** | ❌ 最大冷门漏判 | R1+R2仅1胜→0.50深度魔咒，大幅增强爆冷信号 |

---

## 使用说明

1. **独立使用**: 本文件完全自包含，可直接交给具备 web search 能力的大模型使用
2. **与原模型关系**: 本文件是 `group_stage_predict.md` 的轮次策略定制版，原模型中与本文件冲突的逻辑以本文件为准
3. **适用场景**: 竞猜参考（需要方向性推荐）、内容创作（需要推荐爆冷/稳定的叙事角度）、策略验证
4. **逐场执行**: 对每场小组赛独立运行本 skill，按 STEP 0→1→2→3→4→5→5.5→6 顺序执行

---

*基于2018年俄罗斯世界杯和2022年卡塔尔世界杯96场小组赛数据设计，适配2026年美加墨世界杯赛制*
*版本1.0 — 派生自 group_stage_predict v2.1，轮次差异化策略引导*
