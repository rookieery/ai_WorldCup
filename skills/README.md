# 2026世界杯预测 Skills

两套 AI agent 预测技能，基于2022年卡塔尔世界杯64场比赛数据提炼规律，适配2026年美加墨世界杯赛制。

## Skills 概览

| Skill | 文件 | 核心定位 | 分析粒度 |
|-------|------|---------|---------|
| 小组赛单场预测 | [group_stage_predict.md](group_stage_predict.md) | 赛制约束与博弈 | 单场胜负预测 |
| 小组赛轮次策略预测 | [group_stage_round_strategy.md](group_stage_round_strategy.md) | 轮次差异化策略引导 | R1爆冷/大球 + R2稳定正向 + R3放水/默契球 |
| 淘汰赛单场预测 | [knockout_stage_predict.md](knockout_stage_predict.md) | 球队特质与低容错环境 | 90分钟结果 + 晋级预测（含加时/点球） |
| 淘汰赛阶段策略预测 | [knockout_stage_round_strategy.md](knockout_stage_round_strategy.md) | 阶段差异化策略引导 | R32碾压 + R16特质 + QF黑马 + SF回归 + 3RD经验 + FINAL心理 |

## 2026赛制适配

- **48队 / 12组 / 每组4队**
- 前2名直接出线（24队）+ 8个最好第3名出线 = 32队进淘汰赛
- 出线率 **66.7%**（2022年为50%）
- 新增 1/16 决赛（R32）轮次，共104场比赛

## 数据流

```
group_stage_predict (72场)          group_stage_round_strategy (72场，轮次策略定制版)
    │                                    │
    ├── 每场输出：胜负预测 + 爆冷预警      ├── R1: 爆冷猎手 + 大球雷达
    │                                    ├── R2: 稳定猎手（高置信度正向比分）
    │                                    └── R3: 终局博弈猎手（放水/默契球/生死战）
    │                                    │
    └── 汇总输出：12组最终排名 + 8个最佳第3名
          │
          ▼
knockout_stage_predict (16场)        knockout_stage_round_strategy (淘汰赛阶段策略定制版)
    │                                    │
    ├── 输入：小组赛输出的 group_stage_output   ├── 双支柱硬实力（FIFA排名 + 当年小组赛表现）
    ├── 每场输出：90分钟结果 + 晋级预测         ├── R32: 硬实力碾压猎手（第3名折损）
    │                                    ├── R16: 特质猎手（防守型黑马启动）
    │                                    ├── QF: 黑马猎手（特质权重×1.3）
    │                                    ├── SF: 实力回归猎手（连续加时体能考）
    │                                    ├── 3RD: 经验猎手（深度+经验）
    │                                    └── FINAL: 心理猎手（逆转基因+点球门将）
    │
    └── R32 → R16 → QF → SF → 3RD/FINAL 逐轮递进
```

## 推理链架构

### 小组赛（6步）

| 步骤 | 名称 | 核心产出 |
|------|------|---------|
| STEP 1 | 实力基线评估 | 基础概率表（排名差→胜/平/负） |
| STEP 2 | 爆冷模式识别 | 3种爆冷模式 + upset_boost |
| **STEP 3** | **策略性动机分析** ⭐ | ASS + MDI + MAF（强队不全力争胜的量化） |
| STEP 4 | 第3名出线概率 | 跨组比较 + 安全积分线 |
| STEP 5 | 综合概率合成 | 最终预测 |
| STEP 6 | 淘汰赛路径博弈 | 排名偏好修正（反馈至STEP 3） |

### 淘汰赛（8步，阶段策略版）

| 步骤 | 名称 | 核心产出 |
|------|------|---------|
| STEP 0.5 | 数据源加载 | FIFA排名(支柱A) + 当年小组赛表现GSPI(支柱B) 双支柱 |
| STEP 1 | 硬实力双支柱基线 ⭐ | rank_diff表 + 小组赛势头修正 + 阶段系数 + 连续加时体能考(v1.2) |
| STEP 2 | 爆冷模式+阶段系数 | DEFENSIVE_DARK_HORSE/PENALTY/HOST_FORTRESS + 阶段爆冷倍率 |
| STEP 3 | 动机与心理韧性 | MTI(经验+逆转+点球) + 阶段差异化触发 |
| **STEP 4** | **特质匹配分析** ⭐ | 4种比赛剧本(强攻vs铁桶/双强对攻/稳健互锁/实力悬殊) |
| STEP 5 | 加时/点球决胜 | 门将能力决定点球胜者 |
| STEP 6 | 阶段综合合成 | 90分钟结果 + 晋级预测双层输出 |
| STEP 6.5 | 阶段差异化比分 | 按阶段策略筛选 Top5 比分 |

> 淘汰赛阶段策略删除了小组赛专属步骤（名次价值博弈/第3名出线/路径选择），聚焦"硬实力 + 当年小组赛表现"双支柱。回测校准见 [knockout_stage_round_strategy-2018_backtest.md](knockout_stage_round_strategy-2018_backtest.md) 与 [knockout_stage_round_strategy-2022_backtest.md](knockout_stage_round_strategy-2022_backtest.md)。

## 数据源

- [2022_FIFA_World_Cup_Results.md](../data/2022_FIFA_World_Cup_Results.md) — 2022年卡塔尔世界杯全部64场比赛结果
- [2018_FIFA_World_Cup_Results.md](../data/2018_FIFA_World_Cup_Results.md) — 2018年俄罗斯世界杯全部64场比赛结果
