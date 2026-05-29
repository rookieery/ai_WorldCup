# 任务与问题追踪

> 由 Claude Code 自动生成。追踪未完成任务、问题和改进建议。

---

## 待解决问题

<!-- 格式：### [ISSUE-XXX] 标题 (日期) -->

*（暂无待解决问题）*

---

## 待办任务

<!-- 格式：- [ ] 任务描述 — @上下文 (日期) -->

- [ ] 比赛详情 AI 分析按钮功能实现 — @match-detail-dialog + ai-controller (2026-05-28)
  - 前端：MatchDetailDialog 增加"AI 分析"按钮 + Skill 选择，复用 SSE 流式管道（P5-06）
  - 回调接线 + 移动端适配 + i18n（P5-07）

---

## 改进建议

<!-- 格式：- 💡 建议 — @上下文 (日期) -->

*（暂无建议）*

---

## 已完成

<!-- 格式：- [x] 任务描述 — 完成于 YYYY-MM-DD -->

*（暂无已完成项）*

- [x] P5-04 前端 AI 分析 SSE 客户端 + 类型定义 — 完成于 2026-05-28
  - 新增 `football-web/lib/api/match-analysis.ts`（streamMatchAnalysis + getAvailableSkills）
  - 修改 `football-web/lib/api/ai-chat.ts`（导出 parseSSELines、parseSSEPayload、StreamCallbacks）
- [x] P5-03 后端新增 POST /api/ai/match-analysis + GET /api/ai/skills 端点 — 完成于 2026-05-28
