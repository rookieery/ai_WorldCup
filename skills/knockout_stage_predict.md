# Skill: knockout_stage_predict — 淘汰赛单场预测

## 元信息

- **版本**: 1.0
- **适用赛制**: 2026年世界杯淘汰赛（32强→16强→8强→4强→三四名→决赛）
- **分析粒度**: 单场比赛胜负预测 + 晋级预测（含加时/点球分支）
- **核心定位**: 球队特质与低容错环境
- **上游依赖**: `group_stage_predict` skill 的输出

---

## 输入规范 (Input Schema)

```json
{
  "match": {
    "match_id": "string — 如 'R32_01'",
    "round": "string — 'R32' | 'R16' | 'QF' | 'SF' | '3RD' | 'FINAL'",
    "home_team": "string",
    "away_team": "string"
  },
  "teams": {
    "<team_name>": {
      "fifa_ranking": "integer — 赛前FIFA世界排名",
      "group_stage_output": {
        "group": "string — A-L",
        "group_position": "integer — 1, 2, 或 3",
        "group_points": "integer — 小组赛总积分(3场)",
        "group_goals_for": "integer",
        "group_goals_against": "integer",
        "goal_difference": "integer",
        "group_form": "string — 如 'W-D-W' 或 'L-W-W'",
        "upset_alerts_triggered": "boolean — 小组赛是否触发爆冷预警"
      },
      "team_traits": {
        "defensive_resilience": "integer 1-5 — 防守韧性评级",
        "counter_attack_efficiency": "integer 1-5 — 反击效率评级",
        "set_piece_threat": "integer 1-5 — 定位球威胁评级",
        "penalty_track_record": "integer 1-5 — 点球大战历史表现",
        "comeback_gene": "integer 1-5 — 逆转能力/精神属性",
        "star_player_dependency": "integer 1-5 — 核心球员依赖度(5=极度依赖)",
        "tournament_experience": "integer 1-5 — 大赛经验深度",
        "squad_depth": "integer 1-5 — 阵容深度(淘汰赛多轮次消耗下尤为重要)"
      },
      "key_players_fitness": "string — 伤病情况描述（可选）"
    }
  },
  "tournament_config": {
    "round_config": {
      "R32": { "teams": 32, "advance": 16, "label": "1/16决赛" },
      "R16": { "teams": 16, "advance": 8, "label": "1/8决赛" },
      "QF":  { "teams": 8,  "advance": 4, "label": "1/4决赛" },
      "SF":  { "teams": 4,  "advance": 2, "label": "半决赛" },
      "3RD": { "teams": 2,  "advance": 0, "label": "三四名决赛" },
      "FINAL": { "teams": 2, "advance": 1, "label": "决赛" }
    }
  }
}
```

**team_traits 评分指南**（供 AI agent 参考的定性标准）：

| 特质 | 1分 | 3分 | 5分 |
|------|-----|-----|-----|
| defensive_resilience | 防线脆弱，经常丢球 | 中等水平，偶尔失误 | 铁血防线，极少失误（如2022摩洛哥） |
| counter_attack_efficiency | 反击无力 | 有一定反击能力 | 反击致命高效（如2022法国姆巴佩） |
| set_piece_threat | 定位球无威胁 | 中等 | 定位球是主要得分手段 |
| penalty_track_record | 点球大战经常输 | 五五开 | 点球大战几乎必赢（如2022阿根廷马丁内斯） |
| comeback_gene | 落后即崩盘 | 偶尔能追回 | 经常逆转（如2022阿根廷决赛追平） |
| star_player_dependency | 团队足球 | 有核心但不依赖 | 极度依赖1-2名球星 |
| tournament_experience | 首次参赛或极少经验 | 有一定大赛经验 | 传统豪强，多次深轮次经验 |
| squad_depth | 替补与主力差距大 | 替补可用 | 替补席同样强大（淘汰赛多轮次消耗关键） |

---

## 推理步骤链 (Reasoning Chain)

执行顺序：STEP 1 → STEP 2 → STEP 3 → STEP 4 → STEP 5

---

### STEP 1: 小组赛信号读取 (Group Stage Signal Reading)

**目标**：从小组赛表现中提取信号，作为淘汰赛预测的基础输入。

**执行指令**：

对主队和客队分别执行以下分析：

**信号1：组内排名**

```
if group_position == 1:  ranking_signal = "STRONG";  ranking_boost = +0.05
elif group_position == 2: ranking_signal = "MODERATE"; ranking_boost = 0.00
elif group_position == 3:
    ranking_signal = "WEAK"; ranking_boost = -0.05
    if group_points >= 4:
        // 在竞争激烈的组中以高分排第3，不完全反映实力差
        ranking_signal = "MODERATE_WEAK"; ranking_boost = -0.02
```

**信号2：小组赛势头 (momentum)**

```
// group_form 为3场比赛结果序列，如 "W-D-W"
wins = count('W' in group_form)
draws = count('D' in group_form)
losses = count('L' in group_form)

if wins == 3:   momentum = "PERFECT";   momentum_boost = +0.08
elif wins == 2 AND draws == 1: momentum = "STRONG"; momentum_boost = +0.06
elif wins == 2 AND losses == 1: momentum = "GOOD";  momentum_boost = +0.03
elif wins == 1 AND draws == 2: momentum = "STALE";  momentum_boost = -0.02
elif wins == 1 AND draws == 1 AND losses == 1: momentum = "MIXED"; momentum_boost = 0.00
elif draws >= 2 AND losses >= 1: momentum = "WEAK"; momentum_boost = -0.05
elif losses >= 2: momentum = "TERRIBLE"; momentum_boost = -0.08
```

**信号3：攻防效率**

```
goal_diff_per_match = goal_difference / 3

if goal_diff_per_match >= 2.0:   efficiency = "DOMINANT"; efficiency_boost = +0.06
elif goal_diff_per_match >= 0.5: efficiency = "POSITIVE"; efficiency_boost = +0.03
elif goal_diff_per_match >= 0:   efficiency = "NEUTRAL";  efficiency_boost = 0.00
else:                            efficiency = "NEGATIVE"; efficiency_boost = -0.04
```

**信号4：波动性**

```
if upset_alerts_triggered == true:
    volatility = "VOLATILE"; volatility_boost = -0.02  // 不稳定性是负面信号
else:
    volatility = "STABLE"; volatility_boost = +0.01
```

**合成**：

```
combined_boost = ranking_boost + momentum_boost + efficiency_boost + volatility_boost
```

**输出**：

```json
{
  "step": 1,
  "home_signals": {
    "ranking_signal": "string",
    "momentum": "string",
    "efficiency": "string",
    "volatility": "string",
    "combined_boost": "float"
  },
  "away_signals": { "同上结构" },
  "relative_signal": {
    "home_advantage": "float — home_combined - away_combined",
    "momentum_clash": "string — 描述性文字"
  }
}
```

---

### STEP 2: 特质匹配分析 (Trait Matchup Analysis) ⭐核心步骤

**目标**：分析两队特质的匹配关系，判断哪种比赛风格将主导。这是淘汰赛预测的最关键步骤。

**2022核心洞察**：排名差在淘汰赛中解释力显著下降。克罗地亚(12)淘汰巴西(1)、摩洛哥(22)淘汰西班牙(7)和葡萄牙(9)——排名完全无法解释这些结果，但特质匹配完美解释。

**执行指令**：

根据两队特质组合，识别比赛"风格剧本"：

**剧本A：强攻 vs 铁桶 (ATTACK_VS_FORTRESS)**

```
触发条件：
  一方 counter_attack_efficiency <= 2 且 defensive_resilience <= 2（纯进攻型）
  另一方 defensive_resilience >= 4（铁血防守型）

2022案例：巴西 vs 克罗地亚、西班牙 vs 摩洛哥

分析：
  attack_power = MAX(进攻方的 counter_attack_efficiency, set_piece_threat, 3)
  defense_power = 防守方的 defensive_resilience

  if attack_power >= defense_power + 2:
    outcome = "FAVORED_WIN_90MIN"
    extra_time_probability = 0.20
  elif attack_power >= defense_power:
    outcome = "LIKELY_EXTRA_TIME"
    extra_time_probability = 0.60
    // 2022规律：铁桶方在点球大战中占优（门将通常更突出）
    if 防守方 penalty_track_record >= 4:
      penalty_upset_boost = +0.12
  else:
    outcome = "UPSET_RISK_HIGH"
    extra_time_probability = 0.50
    upset_boost = +0.15
```

**剧本B：双强对攻 (DUAL_ATTACK)**

```
触发条件：
  双方 defensive_resilience <= 3

2022案例：阿根廷 vs 法国（决赛）

分析：
  // 对攻战中 star_player_dependency 高的队占优
  // 因为对攻战就是比谁的关键球员更多次闪光
  if 一方 star_player_dependency >= 4 AND comeback_gene >= 4:
    slight_edge = 该方
  else:
    slight_edge = "NEITHER"
  extra_time_probability = 0.35
```

**剧本C：稳健对稳健 (MUTUAL_SOLIDITY)**

```
触发条件：
  双方 defensive_resilience >= 4

2022案例：摩洛哥 vs 葡萄牙（摩洛哥稳健推进而非纯铁桶）

分析：
  outcome = "LOW_SCORING"
  extra_time_probability = 0.40
  draw_90min_probability = 0.35  // 90分钟平局概率高

  // 谁的反击更致命？
  if home.counter_attack_efficiency > away.counter_attack_efficiency:
    slight_edge = "HOME"
  elif away.counter_attack_efficiency > home.counter_attack_efficiency:
    slight_edge = "AWAY"
  else:
    slight_edge = "NEITHER"
```

**剧本D：实力悬殊 (CLEAR_GAP)**

```
触发条件：
  不满足以上任何剧本条件，且排名差 >= 15

2022案例：英格兰 vs 塞内加尔(3-0)、葡萄牙 vs 瑞士(6-1)

分析：
  if rank_diff >= 25:
    outcome = "STRONG_FAVORITE"
    extra_time_probability = 0.10
  else:
    outcome = "MODERATE_FAVORITE"
    extra_time_probability = 0.25
```

**输出**：

```json
{
  "step": 2,
  "match_script": {
    "type": "ATTACK_VS_FORTRESS | DUAL_ATTACK | MUTUAL_SOLIDITY | CLEAR_GAP",
    "description": "string — 剧本说明",
    "outcome": "string — 预判结果方向",
    "slight_edge": "HOME | AWAY | NEITHER | null",
    "narrative": "string — 人类可读的比赛风格预判"
  },
  "extra_time_probability": "float",
  "penalty_probability": "float — extra_time_probability * 0.83（2022数据：5/6加时进入点球）",
  "trait_driven_adjustments": {
    "upset_boost": "float",
    "draw_boost": "float",
    "favored_win_adjust": "float"
  }
}
```

---

### STEP 3: 轮次压力修正 (Round Pressure Adjustment)

**目标**：不同淘汰赛轮次的压力级别不同，影响比赛风格和爆冷概率。

**2022数据基线**：

| 轮次 | 加时率 | 点球率 | 爆冷率 | 备注 |
|------|--------|--------|--------|------|
| 1/8决赛 | 25% | 25% | 12.5% | 实力差距较大 |
| 1/4决赛 | 37.5% | 25% | 25% | 爆冷率最高轮次 |
| 半决赛+ | 25% | 25% | - | 回归实力 |

**执行指令**：

```
判定当前轮次，应用对应修正：
```

**R32（1/16决赛）——2026新增轮次**：

```
round_pressure = "MODERATE"
round_extra_time_base = 0.20  // 实力差距通常较大，加时概率低

特殊判定：
  if 一方 group_position == 3:
    // 小组第3出线的队通常面对小组第1
    // 但2022证明：爆冷更依赖特质匹配而非排名
    upset_boost = +0.03  // 小幅上调（黑马韧性加成）
```

**R16（1/8决赛）**：

```
round_pressure = "MODERATE_HIGH"
round_extra_time_base = 0.25
upset_boost = 0.00
```

**QF（1/4决赛）——黑马巅峰轮次**：

```
round_pressure = "HIGH"
round_extra_time_base = 0.375
upset_boost = +0.06

// 关键规律：1/4决赛是黑马故事的巅峰
// 到了半决赛，黑马通常力竭（2022摩洛哥半决赛0-2负法国）
// 在此轮次，特质匹配的权重进一步放大
trait_weight_multiplier = 1.3  // 特质分析权重提升30%
```

**SF（半决赛）**：

```
round_pressure = "VERY_HIGH"
round_extra_time_base = 0.25
upset_boost = -0.03  // 到了半决赛的球队都很强，回归实力基本面
```

**3RD（三四名决赛）**：

```
round_pressure = "LOW"
round_extra_time_base = 0.15

// 双方刚输掉半决赛，士气低落
// 大赛经验丰富的队占优
if 一方 tournament_experience >= 4 AND 另一方 < 4:
    experience_boost = +0.08  // 经验丰富方

// 阵容深度在此轮次尤为重要（连续高强度比赛后的疲劳）
if 一方 squad_depth >= 4 AND 另一方 < 3:
    depth_boost = +0.06
```

**FINAL（决赛）**：

```
round_pressure = "EXTREME"
round_extra_time_base = 0.35  // 决赛趋向保守

// 极端压力下，comeback_gene 是最关键的特质
// 2022决赛：阿根廷 vs 法国，双方都有极强逆转基因
if 一方 comeback_gene >= 4:
    comeback_boost = +0.05

// 决赛中大赛经验权重极大
if 一方 tournament_experience >= 4 AND 另一方 <= 2:
    experience_final_boost = +0.10

// 核心球员依赖度在决赛中是双刃剑
if 一方 star_player_dependency >= 4 AND 该核心球员 fitness 有疑虑:
    star_risk = -0.05
```

**输出**：

```json
{
  "step": 3,
  "round_pressure": "string",
  "round_extra_time_base": "float",
  "round_adjustments": {
    "upset_boost": "float",
    "experience_boost_home": "float",
    "experience_boost_away": "float",
    "comeback_boost_home": "float",
    "comeback_boost_away": "float",
    "trait_weight_multiplier": "float — 默认1.0，QF为1.3"
  },
  "narrative": "string"
}
```

---

### STEP 4: 加时/点球决胜预测 (Extra Time & Penalty Prediction)

**目标**：当判定可能进入加时赛后，预测加时赛和点球大战的最终胜者。此步骤合并为"平局决胜"统一输出。

**2022数据基线**：16场淘汰赛中5场进入加时，全部5场都进入点球大战（加时赛内解决率=0%）。点球率=31.25%。

**执行指令**：

```
触发条件：
  extra_time_probability >= 0.25（来自 STEP 2）
  OR match_script.type == "ATTACK_VS_FORTRESS"（铁桶阵剧本天然倾向加时）
  OR round == "FINAL"（决赛天然倾向保守）

if NOT 触发:
  跳过此步骤，直接进入 STEP 5
```

**加时赛预测**：

```
// 2022规律：加时赛中，防守韧性+逆转基因+大赛经验的组合决定胜负
// 6场加时赛中，防守评级更高的队赢了4场

home_et_strength = defensive_resilience * 0.4 + comeback_gene * 0.3 + tournament_experience * 0.3
away_et_strength = defensive_resilience * 0.4 + comeback_gene * 0.3 + tournament_experience * 0.3

diff = home_et_strength - away_et_strength

if diff > 0.5:
    et_predicted_winner = "HOME"
    et_settle_probability = 0.30 + diff * 0.05  // 加时内解决的概率
elif diff < -0.5:
    et_predicted_winner = "AWAY"
    et_settle_probability = 0.30 + abs(diff) * 0.05
else:
    // 差距微小，大概率进入点球
    et_predicted_winner = "TOO_CLOSE"
    et_settle_probability = 0.15  // 大部分进入点球
```

**点球大战预测**：

```
// 2022规律：5场点球大战的决定因素
//   1. 门将能力（penalty_track_record）
//   2. 大赛经验（tournament_experience）
//   3. 心理素质（comeback_gene）

home_penalty_strength = penalty_track_record * 0.4 + tournament_experience * 0.3 + comeback_gene * 0.3
away_penalty_strength = penalty_track_record * 0.4 + tournament_experience * 0.3 + comeback_gene * 0.3

penalty_diff = home_penalty_strength - away_penalty_strength

if penalty_diff >= 1.0:
    penalty_winner = "HOME"
    penalty_confidence = 0.60 + penalty_diff * 0.05
elif penalty_diff <= -1.0:
    penalty_winner = "AWAY"
    penalty_confidence = 0.60 + abs(penalty_diff) * 0.05
else:
    // 差距微小，接近抛硬币
    if penalty_diff > 0: penalty_winner = "HOME"; penalty_confidence = 0.52
    else: penalty_winner = "AWAY"; penalty_confidence = 0.52

// 关键因子标注
key_factor = "goalkeeper_advantage"     if abs(penalty_track_record差) >= 2
          | "experience_advantage"       if abs(tournament_experience差) >= 2
          | "mental_toughness"           if abs(comeback_gene差) >= 2
          | "coin_flip"                  if 所有特质差距 < 1
```

**输出**：

```json
{
  "step": 4,
  "triggered": "boolean",
  "extra_time_probability": "float",
  "penalty_probability": "float",
  "if_extra_time": {
    "predicted_winner": "HOME | AWAY | TOO_CLOSE",
    "settle_in_et_probability": "float — 加时内解决概率",
    "strength_breakdown": {
      "home_et_strength": "float",
      "away_et_strength": "float"
    }
  },
  "if_penalty": {
    "predicted_winner": "HOME | AWAY",
    "confidence": "float 0.50-0.80",
    "key_factor": "string — 决定性因子",
    "strength_breakdown": {
      "home_penalty_strength": "float",
      "away_penalty_strength": "float"
    }
  }
}
```

---

### STEP 5: 综合概率合成与决策 (Final Synthesis)

**目标**：将 STEP 1-4 的输出合成为最终的90分钟预测和晋级预测。

**执行指令**：

#### Part A: 90分钟结果预测

```
// 基础概率（基于排名差，淘汰赛参数）
rank_diff = abs(home.fifa_ranking - away.fifa_ranking)

if rank_diff <= 8:
    // 实力接近，主队略优
    base_home_win = 0.35; base_draw = 0.30; base_away_win = 0.35
elif rank_diff <= 20:
    if home.fifa_ranking < away.fifa_ranking:
        base_home_win = 0.45; base_draw = 0.28; base_away_win = 0.27
    else:
        base_home_win = 0.27; base_draw = 0.28; base_away_win = 0.45
else:
    if home.fifa_ranking < away.fifa_ranking:
        base_home_win = 0.55; base_draw = 0.22; base_away_win = 0.23
    else:
        base_home_win = 0.23; base_draw = 0.22; base_away_win = 0.55

// 叠加 STEP 1 的小组赛信号
signal_diff = home_signals.combined_boost - away_signals.combined_boost
base_home_win += signal_diff * 0.5
base_away_win -= signal_diff * 0.5

// 叠加 STEP 2 的特质匹配调整
// 注意：QF轮次特质权重 ×1.3
trait_multiplier = step3.trait_weight_multiplier  // 默认1.0，QF=1.3
base_home_win += trait_driven_adjustments.favored_win_adjust * trait_multiplier * direction
base_away_win += trait_driven_adjustments.upset_boost * trait_multiplier * direction
base_draw += trait_driven_adjustments.draw_boost * trait_multiplier

// 叠加 STEP 3 的轮次压力调整
base_home_win += (experience_boost_home - experience_boost_away) * 0.3
base_home_win += (comeback_boost_home - comeback_boost_away) * 0.3

// 归一化
total = base_home_win + base_draw + base_away_win
final_home_win = base_home_win / total
final_draw = base_draw / total
final_away_win = base_away_win / total

// 置信度
max_90 = max(final_home_win, final_draw, final_away_win)
confidence_90 = "HIGH" if max_90 >= 0.55 else "MEDIUM" if max_90 >= 0.40 else "LOW"
```

#### Part B: 晋级预测（含加时/点球分支）

```
advance_home = final_home_win   // 90分钟内主队赢
advance_away = final_away_win   // 90分钟内客队赢
draw_case = final_draw          // 90分钟平局，需决胜

if step4.triggered:
    // 平局情况下的晋级分配
    if step4.if_extra_time.predicted_winner == "HOME":
        advance_home += draw_case * step4.if_extra_time.settle_in_et_probability
        draw_remaining = draw_case * (1 - step4.if_extra_time.settle_in_et_probability)
        advance_home += draw_remaining * step4.if_penalty.confidence * (step4.if_penalty.predicted_winner == "HOME" ? 1 : 0)
        advance_away += draw_remaining * step4.if_penalty.confidence * (step4.if_penalty.predicted_winner == "AWAY" ? 1 : 0)
    elif step4.if_extra_time.predicted_winner == "AWAY":
        // 同理，方向相反
    else:  // TOO_CLOSE，大概率进点球
        advance_home += draw_case * step4.if_penalty.confidence * (step4.if_penalty.predicted_winner == "HOME" ? 1 : 0)
        advance_away += draw_case * step4.if_penalty.confidence * (step4.if_penalty.predicted_winner == "AWAY" ? 1 : 0)
else:
    // 加时概率低，但仍需处理平局分支
    // 默认：加时赛中排名更好的队略占优
    favored_in_et = home if home.fifa_ranking < away.fifa_ranking else away
    if favored_in_et == home:
        advance_home += draw_case * 0.55
        advance_away += draw_case * 0.45
    else:
        advance_away += draw_case * 0.55
        advance_home += draw_case * 0.45

// 确定预测晋级方
advancing_team = home if advance_home > advance_away else away
eliminated_team = 另一队

// 确定最可能的决胜方式
method_probabilities = {
    "settle_in_90min": final_home_win + final_away_win,
    "settle_in_extra_time": draw_case * step4.if_extra_time.settle_in_et_probability,
    "settle_in_penalty": draw_case * (1 - step4.if_extra_time.settle_in_et_probability)
}

predicted_method = 概率最高的决胜方式
```

**输出**：

```json
{
  "step": 5,
  "prediction_90min": {
    "result": "home_win | draw | away_win",
    "probabilities": {
      "home_win": "float",
      "draw": "float",
      "away_win": "float"
    },
    "confidence": "HIGH | MEDIUM | LOW"
  },
  "prediction_advance": {
    "advancing_team": "string",
    "advance_probability": "float 0.0-1.0",
    "eliminated_team": "string",
    "eliminated_probability": "float 0.0-1.0",
    "predicted_method": "IN_90MIN | IN_EXTRA_TIME | IN_PENALTY",
    "method_probabilities": {
      "settle_in_90min": "float",
      "settle_in_extra_time": "float",
      "settle_in_penalty": "float"
    }
  }
}
```

---

## 最终输出规范 (Output Schema)

```json
{
  "match_id": "string",
  "round": "string",
  "home_team": "string",
  "away_team": "string",
  "prediction_90min": {
    "result": "home_win | draw | away_win",
    "confidence": "HIGH | MEDIUM | LOW",
    "probabilities": {
      "home_win": "float 0.0-1.0",
      "draw": "float 0.0-1.0",
      "away_win": "float 0.0-1.0"
    }
  },
  "prediction_advance": {
    "advancing_team": "string",
    "advance_probability": "float 0.0-1.0",
    "eliminated_team": "string",
    "eliminated_probability": "float 0.0-1.0",
    "predicted_method": "IN_90MIN | IN_EXTRA_TIME | IN_PENALTY",
    "method_probabilities": {
      "settle_in_90min": "float",
      "settle_in_extra_time": "float",
      "settle_in_penalty": "float"
    }
  },
  "upset_alert": {
    "triggered": "boolean",
    "level": "STRONG | MODERATE | NONE",
    "reasoning": "string"
  },
  "match_script_summary": {
    "script_type": "ATTACK_VS_FORTRESS | DUAL_ATTACK | MUTUAL_SOLIDITY | CLEAR_GAP",
    "narrative": "string — 比赛风格预判（最具叙事价值的信息）"
  },
  "analysis_trace": {
    "step1_group_signals": "object",
    "step2_trait_matchup": "object",
    "step3_round_pressure": "object",
    "step4_extra_time_penalty": "object"
  }
}
```

**关键设计说明**：
- 输出分为两层：**90分钟赛果**和**晋级结果**。淘汰赛允许90分钟内平局，但必须决出晋级者
- `method_probabilities` 不仅预测谁晋级，还预测比赛将以何种方式结束
- `match_script_summary` 中的剧本类型是最具叙事价值的信息

---

## 关键分析因子权重

| 因子 | 权重 | 来源 | 说明 |
|------|------|------|------|
| 排名差 | 20% | 2022淘汰赛16场 | 淘汰赛中排名解释力显著低于小组赛，权重下调 |
| 小组赛信号 | 15% | group_stage_predict 输出 | 排名+势头+攻防效率的复合信号 |
| 特质匹配 | 35% | 2022淘汰赛核心规律 | 最关键因子，QF轮次权重×1.3 |
| 轮次压力 | 15% | 2022各轮次差异 | QF爆冷率最高，SF回归实力 |
| 经验/心理 | 15% | 2022决赛与点球大战 | 越到后面轮次权重越高 |

---

## 2022→2026 规律迁移对照表

| 2022规律 | 2026适配策略 |
|---------|-------------|
| 1/8决赛加时率25% | 可迁移。2026的R32对应2022的R16级别（参赛队从16扩到32） |
| 1/4决赛爆冷率最高 | 直接迁移。QF仍是黑马巅峰轮次，赛制变化不影响 |
| 点球大战中防守型球队占优 | 直接迁移。球队特质决定（2022摩洛哥布努、克罗地亚利瓦科维奇） |
| 半决赛后黑马力竭 | 可迁移。2022摩洛乔半决赛0-2负法国，多一轮R32消耗更大 |
| 决赛极端压力下经验决定胜负 | 直接迁移。淘汰赛永恒规律 |
| 小组赛表现预示淘汰赛走势 | 需改造。2026小组赛含第3名出线队，momentum 信号可靠性需分层处理 |

**2026新增维度**：

| 新维度 | 分析要点 |
|--------|---------|
| 小组第3名的淘汰赛表现 | 首次有8个小组第3名进入淘汰赛，R32中通常面对小组第1，但突围本身就说明有某种强项 |
| 更多轮次=更多消耗 | 2026冠军需打3+5=8场（小组3+淘汰5），比2022多1场R32，阵容深度(squad_depth)更重要 |
| 策略性排名的后效 | 小组赛 skill 的 group_position 预测被淘汰赛直接消费，策略性控制小组排名的博弈链条更长 |

---

## 数据接口：消费 group_stage_predict 输出

本 skill 的 `teams.<team_name>.group_stage_output` 字段直接从 `group_stage_predict` skill 的汇总输出中提取：

```
group_stage_predict 运行完 12组 × 6场 = 72场后，汇总输出：

{
  "group_stage_summary": {
    "groups": {
      "A-L": {
        "final_standings": [
          {
            "position": 1|2|3|4,
            "team": "string",
            "points": "integer",
            "goals_for": "integer",
            "goals_against": "integer",
            "goal_difference": "integer",
            "form": "string — 如 W-D-W",
            "upset_alerts_triggered": "boolean"
          }
        ]
      }
    },
    "best_third_placed": [
      // 按积分>净胜球>进球排序的前8个小组第3名
      {
        "team": "string",
        "group": "string",
        "points": "integer",
        "goal_difference": "integer",
        "advance_ranking": "integer 1-8"
      }
    ]
  }
}
```

**淘汰赛对阵生成规则**（供 AI agent 参考）：

```
R32对阵（2026新增）：
  A组第1 vs B组第2(或其他组合，需参照FIFA官方对阵表)
  各组第1 vs 其他组第2 或 最佳第3名
  ...共16场

R16对阵：
  R32的16个晋级者按固定对阵表配对
  ...共8场

QF/SF/3RD/FINAL 依次类推
```

---

## 回测验证指标

用2022数据回测时，统计以下指标：

| 指标 | 计算方式 | 目标值 |
|------|----------|--------|
| 90分钟结果命中率 | 预测与实际一致的比例 | ≥ 55% |
| 晋级队伍命中率 | 预测晋级与实际一致的比例 | ≥ 60% |
| 爆冷预警准确率 | 触发预警后确实爆冷的比例 | ≥ 40% |
| 加时/点球预测命中率 | 预测进入加时且实际进入的比例 | ≥ 50% |
| Brier Score | 概率预测校准度 | ≤ 0.25 |

---

*基于2022年卡塔尔世界杯16场淘汰赛数据设计，适配2026年美加墨世界杯赛制*
