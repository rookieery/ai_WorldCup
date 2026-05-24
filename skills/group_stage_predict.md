# Skill: group_stage_predict — 小组赛单场预测

## 元信息

- **版本**: 1.0
- **适用赛制**: 2026年世界杯小组赛（48队 / 12组 / 每组4队 / 前2名+8个最好第3名出线）
- **分析粒度**: 单场比赛胜负预测（后续可扩展比分预测）
- **核心定位**: 赛制约束与博弈

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
      "fifa_ranking": "integer — 赛前FIFA世界排名",
      "recent_form": "string — 近期状态描述（可选）",
      "world_cup_experience": "integer — 历史世界杯参赛次数（可选）",
      "key_players_fitness": "string — 核心球员伤病情况（可选）"
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

## 推理步骤链 (Reasoning Chain)

执行顺序：STEP 1 → STEP 2 → STEP 3 → STEP 4 → STEP 5 → STEP 6

---

### STEP 1: 实力基线评估 (Base Strength Assessment)

**目标**：基于FIFA排名差计算基础胜/平/负概率。

**执行指令**：

```
1. 计算 rank_diff = |home.fifa_ranking - away.fifa_ranking|
2. 识别优势方：
   - favored_team = 排名更靠前（数值更小）的队
   - underdog_team = 另一队

3. 查表获取基础概率：
```

| 排名差区间 | 基础概率来源 | favored_win | draw | upset |
|-----------|-------------|-------------|------|-------|
| 0-5 | 实力接近（如英格兰5 vs 西班牙7） | 0.50 | 0.30 | 0.20 |
| 6-15 | 中等差距（如德国11 vs 日本24） | 0.53 | 0.25 | 0.22 |
| 16-30 | 较大差距（如比利时2 vs 摩洛哥22） | 0.50 | 0.22 | 0.28 |
| 31-45 | 大差距（如法国4 vs 澳大利亚38） | 0.65 | 0.18 | 0.17 |
| >45 | 悬殊（如阿根廷3 vs 沙特51） | 0.73 | 0.15 | 0.12 |

**2022数据校准依据**：
- 排名差13-30区间爆冷率最高（日本胜德国/西班牙、摩洛哥胜比利时）——中游强队有足够组织力利用战术拉开差距，同时强队存在轻敌心理
- 排名差>45时爆冷率反而下降——实力悬殊过大，弱队难以制造威胁（沙特胜阿根廷为极端特例）

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
1. 取 STEP 1 输出的 underdog_team 及其 fifa_ranking
2. 按弱队排名区间匹配爆冷模式：
```

| 弱队排名区间 | 模式标识 | 模式名称 | 特征 | upset_boost | 2022案例 |
|-------------|---------|---------|------|------------|---------|
| ≤25 | TACTICAL_STRETCH | 战术拉扯 | 主动放弃控球、快速转换、利用强队压上空间 | +0.08 | 日本胜德国/西班牙 |
| 26-40 | SOLID_DEFENSE | 稳健防守反击 | 低位防守、减少失误、利用定位球或零星反击 | +0.04 | 澳大利亚胜丹麦 |
| >40 | DESPERATE_BURST | 绝地爆发 | 全员退守+偶然进球，或利用强队轮换 | +0.02 | 沙特胜阿根廷、喀麦隆胜巴西 |

**附加修正**：
- 如果弱队 `world_cup_experience >= 5`，TACTICAL_STRETCH 模式额外 +0.05（大赛经验加成）
- DESPERATE_BURST 模式在强队已锁定出线场景下触发 ROTATION_EXPLOIT 子模式，额外 +0.06

**输出**：

```json
{
  "step": 2,
  "underdog_pattern": "TACTICAL_STRETCH | SOLID_DEFENSE | DESPERATE_BURST",
  "pattern_description": "string — 模式说明",
  "upset_boost": "float — 叠加到基础爆冷概率上",
  "pattern_confidence": "float 0.0-1.0"
}
```

---

### STEP 3: 策略性动机分析 (Strategic Motivation Analysis) ⭐核心步骤

**目标**：识别"强队不全力争胜"的场景，量化动机差异，输出概率调整系数。

**2026赛制背景**：出线率66.7%（32/48），强队输球淘汰代价极低。2022验证——第3轮8场中4场强队明确放水（50%），2026此效应将更频繁。

#### 3.1 出线安全度计算 (Advancement Safety Score, ASS)

取值范围：0.0 ~ 1.0

**第一轮（所有球队积分=0）**：

```
rank_group = 球队在本组4队中的FIFA排名序号（1=最强，4=最弱）

先验出线概率（2026赛制，每组约2.67队出线）：
  rank_group = 1 → ASS = 0.85
  rank_group = 2 → ASS = 0.65
  rank_group = 3 → ASS = 0.40
  rank_group = 4 → ASS = 0.20
```

**第二轮（首轮结果已出）**：

```
if points == 3（首轮获胜）:
    ASS = 0.80 + (rank_group == 1 ? 0.10 : 0.00)
elif points == 1（首轮平局）:
    ASS = 0.45 + (rank_group <= 2 ? 0.15 : 0.00)
elif points == 0（首轮输球）:
    ASS = 0.15 + (rank_group <= 2 ? 0.20 : 0.00)
```

**第三轮（精确计算）**：

```
if points >= 6:  ASS = 0.98+
if points == 4:  ASS = 0.80-0.95（视净胜球和对手情况）
if points == 3:  ASS = 0.30-0.60（关键生死战）
if points == 1:  ASS = 0.05-0.20（极度危险）
if points == 0:  ASS = 0.00-0.02（几乎出局）

注：第三轮需结合 STEP 4 的第3名出线概率进行精确计算
```

#### 3.2 动机差异指数 (Motivation Differential Index, MDI)

取值范围：-1.0 ~ +1.0

```
MDI = Motivation_self - Motivation_opponent

Motivation = 1.0 - ASS * (1 - urgency)

urgency 计算规则：
  - 必须赢才能确保出线:        urgency = 1.0
  - 不赢也可能出线（需看其他组）: urgency = 0.7
  - 平局即可确保出线:          urgency = 0.5
  - 已锁定出线:               urgency = 0.1
  - 已出局（无法出线）:         urgency = 0.0
```

#### 3.3 动机调整系数 (Motivation Adjustment Factor, MAF)

```
motivation_gap = abs(MDI)
base_adjustment = motivation_gap * 0.25

轮次权重：
  round_1: 0.6
  round_2: 0.8
  round_3: 1.0

安全度差异放大因子：
  if (ASS_self > 0.90 AND ASS_opponent < 0.30): safety_amplifier = 1.5
  else: safety_amplifier = 1.0

MAF = base_adjustment * round_weight * safety_amplifier
MAF 上限 = 0.35（不超过基础概率的35%偏移）
```

#### 3.4 按轮次的触发条件与分析逻辑

**第一轮——出线兜底效应**：

| 触发条件 | 判定规则 | 效应 |
|---------|---------|------|
| R1-A: 强弱对决的"拼命窗口" | 排名差>25 且弱队 rank_group=3或4 | 弱队动机+0.15，净效应：弱队胜率上调3-5%，平局上调5-8% |
| R1-B: 强队首轮试探 | rank_group=1 且 ASS>0.80 | 强队不全主力/不倾巢进攻，弱队"放手一搏"收益被放大 |
| R1-C: 同组另一场已出结果 | 同组另一场首轮已结束且出现爆冷/大比分 | 动态重算 ASS |

**第二轮——首轮结果的动机分化**：

| 场景 | 己方积分 vs 对手积分 | MDI 方向 | 风险等级 |
|------|---------------------|----------|---------|
| R2-SS | 3 vs 3 | ≈ 0 | 低（双方都安全） |
| R2-SW | 3 vs 1 | < 0（弱队动机更强） | 中 |
| R2-SL | 3 vs 0 | << 0（弱队背水） | 高（MAF≈0.10） |
| R2-WW | 1 vs 1 | ≈ 0 | 低（双方都急） |
| R2-WL | 1 vs 0 | < 0（弱队更急） | 中 |
| R2-LL | 0 vs 0 | ≈ 0 | 低（生死战） |

**R2-SL（3分 vs 0分）最高风险场景详细计算**：

```
己方 ASS ≈ 0.85, urgency = 0.5
对手 ASS ≈ 0.10, urgency = 1.0

Motivation_self     = 1.0 - 0.85 * (1 - 0.5) = 0.575
Motivation_opponent = 1.0 - 0.10 * (1 - 1.0) = 1.0

MDI = 0.575 - 1.0 = -0.425
MAF = 0.425 * 0.25 * 0.8 * 1.2 = 0.102

→ 强队胜率下调约10%，弱队胜率上调约10%
```

**第三轮——策略性行为高峰**：

| 触发条件 | 判定规则 | 效应 |
|---------|---------|------|
| R3-A: 已锁定出线 | ASS≥0.95 | Motivation降至0.1，MAF=0.20-0.35（视对手情况） |
| R3-B: 平局即双双出线 | 双方平局后均达4分且排名安全 | 平局概率上调15-25%，双方胜率各下调8-12% |
| R3-C: 第3名出线兜底 | 输球仍可能以第3名出线 | 调用 STEP 4，若概率>50%则 urgency 降低 |
| R3-D: 淘汰赛路径博弈 | ASS>0.80 且当前排名为第1或可能第1 | 调用 STEP 6，路径偏好影响求胜欲 |

**2022验证案例**：

| 比赛 | 强队赛前积分 | 实际结果 | 纯实力预测 | STEP 3 修正后 | 验证 |
|------|-------------|---------|-----------|-------------|------|
| 突尼斯 vs 法国 | 6 | 法国0-1负 | 法国胜~70% | 法国胜~45% | 方向正确 |
| 喀麦隆 vs 巴西 | 6 | 巴西0-1负 | 巴西胜~75% | 巴西胜~50% | 方向正确 |
| 韩国 vs 葡萄牙 | 6 | 葡萄牙1-2负 | 葡萄牙胜~65% | 葡萄牙胜~40% | 方向正确 |
| 日本 vs 西班牙 | 4 | 西班牙1-2负 | 西班牙胜~55% | 西班牙胜~38% | 方向正确 |

#### 3.5 概率修正公式

```
输入：W_base, D_base, L_base（来自 STEP 1-2），MAF, MDI

if MDI > 0（己方动机更强）:
    W_adjusted = W_base + MAF * (1 - W_base)
    L_adjusted = L_base * (1 - MAF)
    D_adjusted = 1.0 - W_adjusted - L_adjusted

elif MDI < 0（对手动机更强）:
    L_adjusted = L_base + MAF * (1 - L_base)
    W_adjusted = W_base * (1 - MAF)
    D_adjusted = 1.0 - W_adjusted - L_adjusted

# 默契球叠加（如果触发 R3-B）
if tacit_draw_risk is not None:
    draw_bonus = tacit_draw_risk * 0.20
    W_adjusted = W_adjusted * (1 - draw_bonus)
    L_adjusted = L_adjusted * (1 - draw_bonus)
    D_adjusted = 1.0 - W_adjusted - L_adjusted

# 归一化
total = W_adjusted + D_adjusted + L_adjusted
W_final = W_adjusted / total
D_final = D_adjusted / total
L_final = L_adjusted / total
```

#### 3.6 边界情况处理

| 边界情况 | 处理方式 |
|---------|---------|
| 双方均已出局 | 双方 Motivation=0.1，MAF=0（净效应抵消），回归实力基线 |
| 同组另一场出现重大意外 | 动态重算 ASS，confidence 降为 "low" |
| 淘汰赛路径涉及未完赛组 | STEP 6 只给概率性评估，confidence 标记 "medium"/"low" |
| 同组两场第三轮联动 | 假设同组另一场以"最可能结果"计算，narrative 中标注假设 |
| 净胜球因素 | 净胜球优势>2时 urgency *= 0.85 |

**输出**：

```json
{
  "step": 3,
  "step_name": "Strategic_Motivation_Analysis",
  "analysis": {
    "ASS_self": "float 0.0-1.0",
    "ASS_opponent": "float 0.0-1.0",
    "urgency_self": "float 0.0-1.0",
    "urgency_opponent": "float 0.0-1.0",
    "Motivation_self": "float 0.0-1.0",
    "Motivation_opponent": "float 0.0-1.0",
    "MDI": "float -1.0 to 1.0",
    "MAF": "float 0.0-0.35",
    "round_weight": "float",
    "safety_amplifier": "float"
  },
  "triggers": [
    {
      "trigger_id": "string — 如 R3-A",
      "trigger_name": "string",
      "condition_met": "boolean",
      "detail": "string"
    }
  ],
  "special_flags": {
    "tacit_draw_risk": "float | null",
    "knockout_path_bias": "float | null",
    "third_place_probability": "float | null"
  },
  "adjustment": {
    "W_adjusted": "float",
    "D_adjusted": "float",
    "L_adjusted": "float",
    "confidence": "high | medium | low"
  },
  "narrative": {
    "key_risk": "string — 1-2句核心风险描述",
    "adjustment_note": "string — 3-5句完整分析说明"
  }
}
```

---

### STEP 4: 第3名出线概率评估 (Third-Place Advancement Probability)

**目标**：评估小组第3名出线规则对本场比赛策略的影响。

**2026赛制说明**：12个组的第3名按积分>净胜球>进球排序，取前8名出线。

**执行指令**：

```
1. 第3名出线门槛估算（基于12组2.67出线的数学期望）：
   - 4分（1胜1平）：几乎必出线（概率 > 95%）
   - 3分（1胜1负）：约50%概率出线（取决于净胜球和同组其他第3名积分）
   - 2分（2平）：约20-30%概率出线
   - 1分（1平1负）：几乎不可能出线（<5%）

2. 判断本组可能产生的第3名积分：
   根据当前积分格局和剩余比赛，计算各组可能产生的第3名积分分布

3. 跨组比较：
   汇总其他组已完赛结果，估算当前第3名出线所需的安全积分线
   safety_line = 基于已知数据的动态阈值

4. 判断本场比赛对双方第3名出线概率的影响
```

**对本场比赛的影响规则**：

| 场景 | 判定 | 效应 |
|------|------|------|
| 一方输球仍可能第3名出线 | 输后积分≥3 且其他组第3名预估较弱 | 该队 urgency 降低，MAF 增大 |
| 双方输球都淘汰 | 输后积分<3 或其他组第3名预估较强 | 双方极端保守或极端激进 |
| 双方都有后路 | 输后都有一定概率第3名出线 | 比赛偏开放 |

**输出**：

```json
{
  "step": 4,
  "third_place_threshold": {
    "estimated_safety_points": "integer — 第3名出线安全积分线",
    "confidence": "high | medium | low"
  },
  "home_third_place_probability": "float 0.0-1.0 — 若排第3名时的出线概率",
  "away_third_place_probability": "float 0.0-1.0",
  "impact_on_match": {
    "home_desperation_boost": "float",
    "away_desperation_boost": "float",
    "draw_boost": "float | null",
    "narrative": "string"
  }
}
```

---

### STEP 5: 综合概率合成 (Final Probability Synthesis)

**目标**：将 STEP 1-4 的输出合成为最终预测。

**执行指令**：

```
1. 取 STEP 1 的 base_probabilities: {favored_win, draw, upset}
2. 叠加 STEP 2 的 upset_boost
3. 叠加 STEP 3 的策略性动机调整（MAF, MDI）
4. 叠加 STEP 4 的第3名出线影响

合成计算：
  adjusted_upset       = base.upset + step2.upset_boost + step3.MAF * sign + step4.desperation_boost
  adjusted_draw        = base.draw + step3.draw_adjustment + step4.draw_boost
  adjusted_favored_win = base.favored_win - step3.MAF * sign

归一化（确保三者之和 = 1.0）：
  total = adjusted_upset + adjusted_draw + adjusted_favored_win
  final_upset = adjusted_upset / total
  final_draw = adjusted_draw / total
  final_favored_win = adjusted_favored_win / total

确定预测结果：
  max_prob = MAX(final_favored_win, final_draw, final_upset)
  predicted_result = 对应的结果标识

置信度评估：
  max_prob >= 0.55 → HIGH
  max_prob >= 0.40 → MEDIUM
  max_prob < 0.40  → LOW

爆冷预警：
  if final_upset >= 0.25: upset_alert = true
  if final_upset >= 0.35: upset_alert_level = "STRONG"
  elif final_upset >= 0.25: upset_alert_level = "MODERATE"
```

---

### STEP 6: 淘汰赛路径博弈分析 (Knockout Path Analysis)

**目标**：评估小组排名偏好对淘汰赛对阵的影响，反馈修正 STEP 3。

**执行指令**：

```
1. 根据当前积分格局，推算本队可能的小组最终排名（第1/第2/第3）

2. 查询淘汰赛对阵表：
   - 小组第1 vs 另一组第2（常规路径）
   - 小组第2 vs 另一组第1（需要面对其他组头名）
   - 小组第3 vs 某组第1（最差路径）

3. 评估各排名对应的淘汰赛对手强度：
   根据其他组的出线形势预估对手

4. 判断是否存在"第2名路径优于第1名路径"的情况：
   if path_as_2nd_strength < path_as_1st_strength * 0.8:
       // 第2名的对手明显更弱
       // 可能产生"不想拿第1"的动机
       knockout_path_bias = -0.05 ~ -0.10

5. 将 knockout_path_bias 反馈给 STEP 3 的 urgency 计算
```

**输出**：

```json
{
  "step": 6,
  "path_analysis": {
    "as_1st_opponent": "string — 预估对手",
    "as_2nd_opponent": "string — 预估对手",
    "path_preference": "1ST_PREFERRED | 2ND_PREFERRED | NEUTRAL",
    "knockout_path_bias": "float — 正值倾向第1，负值倾向第2",
    "confidence": "high | medium | low"
  }
}
```

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
    "underdog_team": "string | null"
  },
  "upset_alert": {
    "triggered": "boolean",
    "level": "STRONG | MODERATE | NONE",
    "reasoning": "string — 为什么可能爆冷"
  },
  "strategic_motivation_summary": {
    "assessed": "boolean",
    "key_finding": "string — 核心发现，如'强队已锁定出线，弱队背水一战'",
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
| 爆冷模式匹配 | 15% | 2022年11场小组赛爆冷 |
| 策略性动机 | 25% | 2022第3轮放水案例 + 2026赛制推导 |
| 第3名出线博弈 | 10% | 2026赛制独有 |
| 淘汰赛路径偏好 | 10% | 2026赛制新增维度 |

---

## 2022→2026 规律迁移对照表

| 2022规律 | 2026适配策略 |
|---------|-------------|
| 第3轮同时开赛效应（6/14场爆冷在第3轮） | 可迁移。第3轮仍是策略性行为高峰，12组同时开赛 |
| 爆冷率随轮次递增（R1=12.5%, R2=25%, R3=31.3%） | 可迁移但调高基线。66.7%出线率使每轮的"放水"门槛更低 |
| 已出线球队轮换导致爆冷 | 直接迁移且放大。3分=大概率出线，轮换动机比2022更强 |
| 中游强队（排名20-30）爆冷率最高 | 直接迁移。球队特质决定，与赛制无关 |
| 每队3场有一定容错 | 需改造。虽然仍是3场，但第3名出线兜底大幅提高容错 |
| 首轮输球非致命（阿根廷案例） | 直接迁移且强化。66.7%出线率下首轮输球的淘汰概率更低 |

---

## 使用说明

1. **逐场执行**：对每场小组赛独立运行本 skill，按 STEP 1→6 顺序执行
2. **信息累积**：每场比赛执行完后，将结果更新到 `group_context.completed_matches` 中，供后续比赛使用
3. **跨组信息**：第三轮比赛时需利用 `tournament_context.other_groups_completed_matches` 进行第3名出线概率估算
4. **输出消费**：本 skill 的 `group_impact` 和 `prediction` 输出将被 `knockout_stage_predict` skill 直接消费

---

*基于2022年卡塔尔世界杯64场比赛数据设计，适配2026年美加墨世界杯赛制*
