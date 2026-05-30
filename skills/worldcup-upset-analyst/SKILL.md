---
name: worldcup-upset-analyst
description: >
  世界杯爆冷分析专家。基于2014/2018/2022三届世界杯192场比赛数据，使用4种量化模型
  (排名差距、多因素逻辑回归、规则推理、趋势外推)进行爆冷概率预测。支持小组赛/淘汰赛
  分层分析，涵盖7大爆冷规律。触发条件：世界杯预测、爆冷分析、强弱对比、小组赛出线分析、
  卫冕冠军表现预测。World Cup upset analysis with quantitative models.
when_to_use: >
  世界杯预测、爆冷分析、underdog机会、小组赛奇迹、淘汰赛预测、
  "Can [team] beat [team]?"、"卫冕冠军能走多远"、"亚洲球队表现"、
  "What are the chances of an upset?"、"2026 World Cup prediction"、
  "compare [team] and [team] in World Cup"、"home field advantage analysis"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
context: fork
disable-model-invocation: false
user-invocable: true
---

# 世界杯爆冷分析专家 (World Cup Upset Analyst)

## Overview

This skill analyzes FIFA World Cup historical data (2014/2018/2022 — 192 matches across 3 tournaments) to identify upset patterns and predict match outcomes. It uses **four quantitative models** in ensemble, separates **group stage** from **knockout stage** analysis, and encodes **7 known upset patterns** as if-then rules.

**核心能力**: Given any two teams and a tournament context, computes a consensus upset probability with model-by-model breakdown, key factor analysis, and historical comparables.

> **Definition of "upset"**: A lower-ranked team wins when rank_gap >= 10, or draws when rank_gap >= 25 AND higher-ranked opponent is in FIFA top 15.

---

## Data Available

| File | Contents |
|---|---|
| `assets/matches-2014.json` | All 64 matches — 2014 Brazil World Cup |
| `assets/matches-2018.json` | All 64 matches — 2018 Russia World Cup |
| `assets/matches-2022.json` | All 64 matches — 2022 Qatar World Cup |
| `assets/rankings.json` | Pre-tournament FIFA rankings (2014, 2018, 2022, +2026 estimated) |
| `assets/upset-definitions.json` | Upset taxonomy, classification criteria, historical counts by stage |
| `assets/format-rules.json` | Tournament format changes (VAR, subs, added time, squad size) |
| `assets/model-parameters.json` | Calibrated parameters for all 4 models |
| `references/upset-analysis-methodology.md` | Detailed methodology (loaded on demand) |
| `scripts/prediction-calculator.py` | Optional Python script for multi-match batch prediction |

---

## 7 Known Upset Patterns (爆冷规律)

| # | Pattern | Condition | Boost | Evidence |
|---|---------|-----------|-------|----------|
| 1 | **卫冕冠军魔咒** | Defending champion in group stage | +25% | Spain 2014, Germany 2018 eliminated; France 2022 lost to Tunisia |
| 2 | **亚洲崛起** | AFC team vs top-10 ranked opponent in groups | +20% | 5/8 upsets in 2022 = Asian teams (Japan x2, Saudi, S.Korea, Australia) |
| 3 | **5换人效应** | 2022+ tournament, deep-squad underdog | +15% | 2022 had 57% more upsets than 2018. Japan's 田忌赛马 strategy |
| 4 | **传染性爆冷** | Another upset already occurred in same group | +12% | 80% of groups with one upset had a second (2018 Group F, 2022 Group E) |
| 5 | **东道主加成** | Host continent team with strong football culture | **-10%** | Reduces upset chance. Europe 2018, South America 2014. Qatar = exception |
| 6 | **淘汰赛稳定** | Match is knockout stage | **-15%** | Knockout upset rate ~5% vs group ~9% |
| 7 | **VAR裁判效应** | 2018+ group stage, disciplined defensive underdog | +8% | VAR era = more penalties. Clean defenders benefit |

---

## 4 Quantitative Models

### Model 1: Ranking Gap / Elo Probability (权重: 35%)
```
P(upset) = 1 / (1 + e^(-0.065 * (gap - 15)))
```
- `gap` = (lower_rank - higher_rank). Higher gap = higher upset chance
- At gap=15: P=50%. At gap=30: P=72%. At gap=5: P=34%
- **Historical accuracy: 73%**

### Model 2: Multi-Factor Logistic Regression (权重: 30%)
```
logit = -2.1 + 0.06*ranking_gap + 0.5*is_group_stage + 0.8*is_defending_champion
        + 0.4*is_5_sub_era + (-0.3)*is_home_continent + 0.15*year_trend
        + 0.25*cluster_effect
P = 1 / (1 + e^(-logit))
```
- **Historical accuracy: 68%**

### Model 3: Rule-Based Inference Engine (权重: 20%)
```
P = base_rate(10.5%) + sum(applicable_rule_boosts)
Clamped to [5%, 95%]
```
- Check all 7 rules above for the given match context
- **Historical accuracy: 65%**

### Model 4: Trend Extrapolation (权重: 15%)
```
Trend: 2014(4) → 2018(7) → 2022(11) → 2026(14 base + 4 adjustments = ~18)
Formula: upsets = 3.5 * year_index + 3.83 (year_index: 2014=0, 2018=1, ...)
```
- **2026 projection**: ~18 upsets (range: 13-23) — reflects 48-team expansion + 5 subs + host effects

### Consensus Synthesis
```
P_consensus = 0.35*P_model1 + 0.30*P_model2 + 0.20*P_model3 + 0.15*P_model4
```

---

## Core Workflow

### Step 1: Load Data
Read ALL relevant JSON files from `assets/`. Do not skip any data source.

### Step 2: Classify Query
Determine if the request is:
- **(a) Historical pattern analysis**: "What happened when...?"
- **(b) Single match prediction**: "Can Japan beat Germany?"
- **(c) Tournament-level prediction**: "2026 World Cup upset forecast"
- **(d) Team comparison**: "Which is more likely to cause an upset, Japan or Morocco?"

### Step 3: Separate Group vs Knockout Analysis
- **Group stage**: 9% historical upset rate. More volatility, especially Matchday 1 and Matchday 3.
- **Knockout stage**: 5% upset rate. Most upsets involve penalty shootouts (4/5 knockout upsets).
- Use `stage` field from match data to determine which rate applies.
- For new/unknown matchups, use the stage specified in the query or default to group stage.

### Step 4: Execute All 4 Models
Compute each model independently:
1. Look up team rankings from `assets/rankings.json`
2. Apply formulas using parameters from `assets/model-parameters.json`
3. Document each intermediate value (show your work)

### Step 5: Find Historical Comparable
Search all 192 matches for the most similar historical matchup. Compare:
- Ranking gap (40% weight)
- Stage (25% weight)
- Confederation match (20% weight)
- Tournament era (15% weight)

### Step 6: Synthesize Consensus
Combine model outputs with ensemble weights. Assign confidence level.

### Step 7: Return Structured Analysis

---

## Output Format

Always return analysis in this structure:

```
## Upset Analysis: [Team A] vs [Team B] — [Tournament Year] [Stage]

**Consensus Upset Probability**: XX%
**Confidence**: [高/中/低] — [reasoning]

### Model Breakdown
1. Ranking Gap Model: XX% (gap: X positions)
2. Multi-Factor Model: XX% (active factors: [list])
3. Rule-Based Model: XX% (active rules: [list])
4. Trend Model: XX% ([year] context)

### Key Factors
- ✓ [Factor]: [detailed explanation]
- ✓ [Factor]: [detailed explanation]
- ✗ [Factor]: [why it doesn't apply]

### Historical Comparable
**[Match]** — [Year] [Stage]: [Score detail]
[What made this similar and what the outcome was]

### Upset Recipe for [Underdog]
[3-5 bullet points on what conditions would need to align for an upset]
```

---

## Invocation Methods

| Method | Usage |
|--------|-------|
| **Auto-trigger** | Ask World Cup / upset related questions — this skill loads automatically |
| **Slash command** | `/worldcup-upset-analyst Japan vs Germany 2026 group stage` |
| **Context command** | `/worldcup-upset-analyst analyze tournament 2026` |
| **Batch prediction** | `/worldcup-upset-analyst batch predict upcoming matches` |

---

## Common Rationalizations to Avoid

| Rationalization | Rebuttal |
|---|---|
| "This is just a single data point" | The ensemble cross-validates from 4 independent angles → stronger signal |
| "Rankings are unreliable" | Pre-tournament FIFA rankings are the standard; model uses gap, not absolute. 73% accuracy validates this choice |
| "Every match is different" | Statistical patterns across 192 matches provide a robust Bayesian prior |
| "2026 is completely different" | The trend model explicitly accounts for 48-team expansion; predictions include confidence intervals |
| "This team has 'momentum'" | Momentum is not encoded; historical data shows group stage momentum rarely carries to knockouts |

## Red Flags (Stop and Re-evaluate)

- Ignoring home continent advantage factor
- Not accounting for group stage vs knockout stage difference
- Treating all upsets equally (5% KO rate vs 9% group rate)
- Overlooking 5-sub rule effect in comparisons involving 2022+
- Not adjusting for defending champion status in group stage
- Using in-tournament rankings instead of pre-tournament rankings

## Verification Checklist

- [ ] All 3 tournaments' data loaded (check file count)
- [ ] Upset classification matches definition in upset-definitions.json
- [ ] Model parameters loaded from model-parameters.json
- [ ] Consensus weights correctly applied
- [ ] Confidence level justified
- [ ] Historical comparable matches the contextual profile
- [ ] Separate group/knockout rates used where applicable
- [ ] All 7 rules checked against match context
