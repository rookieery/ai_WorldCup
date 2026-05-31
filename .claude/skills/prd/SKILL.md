---
name: prd
description: 根据功能描述生成结构化 PRD 文档，产出 Ralph Stories 格式的 User Stories。
allowed-tools: Read, Write, Glob, Grep
---

# PRD Generator Skill

## 上下文
- 项目规范：@CLAUDE.md
- 架构速查：@.docs/agent-file-map.md
- 组件速查：@.docs/agent-component-map.md
- API 速查：@.docs/agent-api-reference.md
- 业务概览：@.docs/business-overview.md

## 触发场景

当用户表达以下意图时激活：
- "帮我写一个 PRD"
- "规划一下 XX 功能"
- "把 XX 需求拆成 User Stories"
- "创建 PRD" / "写 PRD" / "需求文档"

## 执行流程

### 阶段 1：澄清需求（必须执行）

向用户提出 3-5 个关键问题，每个问题提供 2-4 个选项（使用字母编号 A/B/C/D），方便用户快速回复（如 "1A, 2C, 3B"）。

问题维度：
1. **核心目标**：这个功能主要解决什么问题？
2. **功能范围**：包含哪些子功能？哪些明确不做？
3. **用户角色**：面向哪类用户？
4. **成功标准**：怎样算"做好了"？
5. **技术偏好**（可选）：前后端分工、是否需要新 API 等

**如果用户已提供了充分信息**（如从 Planner 输出转来），可以跳过提问阶段，直接进入生成。

### 阶段 2：查阅项目上下文（必须执行）

在生成 PRD 前，必须查阅以下项目文件以确保 Story 的可行性：
1. 读取 `.docs/agent-file-map.md` — 了解现有文件结构
2. 读取 `.docs/agent-component-map.md` — 了解可复用的组件
3. 读取 `.docs/agent-api-reference.md` — 了解现有 API 端点
4. 根据功能范围，选择性读取相关源码以确认现有模式

### 阶段 3：生成结构化 PRD

输出格式必须严格遵循以下结构：

```markdown
# PRD: [功能名称]

## 概述 (Overview)
[2-3 句话总结功能目标和价值]

## 目标 (Goals)
- [目标 1，可衡量]
- [目标 2，可衡量]

## 用户故事 (User Stories)

### US-001: [Story 标题]
- **Description**: As a [角色], I want [功能] so that [收益]
- **Acceptance Criteria**:
  1. [可验证的具体条件]
  2. [可验证的具体条件]
  3. TypeScript 项目构建通过 (`npm run build` 无错误) / Python 类型检查通过
- **Priority**: 1

### US-002: [Story 标题]
...

## 功能需求 (Functional Requirements)
- FR-1: [需求描述]
- FR-2: [需求描述]

## 非目标 (Non-Goals)
- [明确不在本次范围内的功能]
- [延后处理的事项]

## 设计考虑 (Design Considerations)
- [UI/UX 相关的约束或建议]

## 技术考虑 (Technical Considerations)
- [架构、性能、安全相关的建议]

## 成功指标 (Success Metrics)
- [ ] [可量化的指标 1]
- [ ] [可量化的指标 2]

## 待确认问题 (Open Questions)
- [需要进一步讨论的决策点]
```

### 阶段 4：保存 PRD

将生成的 PRD 保存到 `tasks/prd-[feature-name].md`（文件名使用 kebab-case）。

## Story 粒度规则（核心）

1. **一个 Story = 一个 Ralph 迭代**：每个 Story 必须在单次 AI 会话（一个 context window）中可完成。
2. **合理的粒度参考**：
   - ✅ "创建 Team 数据模型和 Schema"
   - ✅ "添加比赛列表页面组件"
   - ✅ "实现预测 API 端点"
   - ❌ "搭建整个认证系统"（太大）
   - ❌ "修改一个 CSS 类名"（太小，应合并）
3. **依赖排序**：Priority 数字越小越先执行。顺序：Schema/DB → Service → Controller → UI → 集成。
4. **验收标准可验证**：
   - ✅ "GET /api/teams 返回 200 并包含 name 和 name_zh 字段"
   - ✅ "点击预测按钮后显示概率进度条"
   - ❌ "功能正常工作"
   - ❌ "用户体验良好"
5. **构建检查**：每条 Story 最后一条验收标准必须是构建/类型检查通过。
6. **UI Story**：涉及界面变更的 Story 必须包含 "通过浏览器验证布局和主题一致性"。

## 国际化要求

- PRD 中涉及的用户可见文本必须标注需通过 i18n key 引用
- 队伍名、场馆名等需同时提供 `name` 和 `name_zh`
- 验收标准中应体现中英文双语支持

## 从 Planner 输出转换（特殊场景）

当用户明确表示"把 Planner 的方案转为 PRD"或提供了 Planner 的实施计划时：
1. 跳过阶段 1（需求已明确）
2. 直接从 Planner 的实施步骤中提炼 User Stories
3. 每个实施阶段提炼为 1-2 条 Story
4. 保留 Planner 中的文件路径信息在 Story Description 中
5. 验收标准从 Planner 的成功标准和测试策略中提炼

## 输出确认

生成完成后，向用户展示：
1. Story 总数和预计迭代次数
2. 关键依赖关系图（如有跨 Story 依赖）
3. 询问用户是否需要调整 Story 粒度或顺序
4. 提示用户可以运行 `/ralph` 将 PRD 转换为 `prd.json`
