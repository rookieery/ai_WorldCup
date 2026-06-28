# .docs/ — 2026 世界杯项目文档

> AI Agent 速查索引。代码变更时请同步更新本文档。

## 快速导航

| 文档 | 用途 |
|------|------|
| [agent-file-map.md](agent-file-map.md) | 文件导航："X 在哪里？" |
| [agent-component-map.md](agent-component-map.md) | React 组件注册表 |
| [agent-api-reference.md](agent-api-reference.md) | 后端 API 契约（已实现） |
| [business-overview.md](business-overview.md) | 业务逻辑与数据流 |
| [todo.md](todo.md) | 任务与问题追踪 |

## 项目关键参考文件

| 文件 | 内容 |
|------|------|
| **`BUSINESS.md`** | **项目业务全景文档（权威来源）**：整合前后端需求、API 契约、数据模型、实施计划 |
| `CLAUDE.md` | 工程规范与编码标准 |
| `football-web/REQUIREMENTS.md` | 前端 PRD（功能、数据模型、UI 规格） |
| `football-server/scalable-beaming-riddle.md` | 后端架构方案 |
| `data/2026_FIFA_World_Cup_Group_Stage.md` | 2026 小组赛赛程原始数据 |
| `data/2026_FIFA_World_Cup_Round_of_32.md` | 2026 1/16决赛（32强淘汰赛）赛程（16场对阵全部确定，截至6/28） |
| `data/2022_FIFA_World_Cup_Results.md` | 历史比赛结果 |
| `skills/group_stage_predict.md` | AI 预测技能（小组赛） |
| `skills/knockout_stage_predict.md` | AI 预测技能（淘汰赛） |
| `skills/冠亚军分析.md` | AI 预测技能（冠亚军预测 v2.2：11大策略 + 5步推理链 + 2018+2022双重复测校准） |
| `skills/冠亚军分析-2022回测.md` | 2022世界杯回测分析（10轮×1000次蒙特卡洛，校准策略六/八/九） |
| `skills/冠亚军分析-2018回测.md` | 2018世界杯回测分析（10轮×1000次蒙特卡洛，发现东道主效应/卫冕魔咒/死亡半区溢价） |
| `.claude/skills/prd/SKILL.md` | `/prd` Skill — 根据功能描述生成结构化 PRD 文档 |
| `.claude/skills/ralph/SKILL.md` | `/ralph` Skill — 将 PRD 转换为 prd.json（Ralph 自动循环消费） |
| `.claude/agents/planner.md` | Planner Subagent — 复杂功能技术级实施规划（含 Ralph Stories 输出） |
