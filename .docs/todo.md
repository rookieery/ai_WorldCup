# 任务与问题追踪

> 由 Claude Code 自动生成。追踪未完成任务、问题和改进建议。

---

## 待解决问题

<!-- 格式：### [ISSUE-XXX] 标题 (日期) -->

### [ISSUE-001] monte_carlo_finals.py 超过 600 行硬限制 (2026-05-30)
- 文件 `football-server/scripts/monte_carlo_finals.py` 当前 716 行，超出 600 行硬限制
- 需委派 refactor-expert 子智能体进行模块化拆分（模拟引擎 / 策略模型 / 结果输出）

---

## 待办任务

<!-- 格式：- [ ] 任务描述 — @上下文 (日期) -->

- [ ] 比赛详情 AI 分析按钮功能实现 — @match-detail-dialog + ai-controller (2026-05-28)
  - 前端：MatchDetailDialog 增加"AI 分析"按钮 + Skill 选择，复用 SSE 流式管道（P5-06）
  - 回调接线 + 移动端适配 + i18n（P5-07）

---

## 改进建议

<!-- 格式：- 💡 建议 — @上下文 (日期) -->

- 💡 [高] 新增"附加赛/资格赛淬炼"平局加成因子：附加赛晋级队触发额外 draw_boost。依据：2026 R1 B组波黑、卡塔尔两支附加赛队伍均逼平排名更高的对手（加拿大1-1、瑞士1-1），导致两场 HIGH 置信度强队胜翻车。@skills/group_stage_round_strategy.md (2026-06-15)
- 💡 [中] CAF/AFC 球队"五大联赛球员占比高"时上调 TACTICAL_STRETCH 触发概率。依据：E_M2 科特迪瓦 1-0 厄瓜多尔爆冷未被预警。@skills/group_stage_round_strategy.md (2026-06-15)
- 💡 [中] 大球信号对"实力有差距"场次上调进球量级预估。依据：D_M1 美国4-1、F_M2 瑞典5-1、E_M1 德国7-1 均大幅超出预期进球数。@skills/group_stage_round_strategy.md (2026-06-15)

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
