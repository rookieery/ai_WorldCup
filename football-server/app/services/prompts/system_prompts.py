"""System prompt fragments and analysis prompt templates.

Contains the bilingual (zh-CN / en-US) system prompt fragments used to
construct the AI role description, tournament context, and analysis
instruction prompts.  These were extracted from ``prompt_builder.py`` to
keep that module under the 600-line hard-limit.
"""

from __future__ import annotations

from typing import Dict


# ---------------------------------------------------------------------------
# Language-aware system prompt fragments
# ---------------------------------------------------------------------------

SYSTEM_FRAGMENTS: Dict[str, Dict[str, str]] = {
    "zh-CN": {
        "role_description": (
            "你是 2026 年 FIFA 世界杯 AI 分析助手。你精通足球赛事分析，"
            "能够基于 FIFA 排名、球队特质、历史数据和赛制约束进行专业预测和解读。"
        ),
        "tournament_context": (
            "赛事背景：2026 年美加墨世界杯\n"
            "- 48 支球队 / 12 个小组 / 每组 4 队\n"
            "- 小组前 2 名 + 8 个最佳第 3 名出线（共 32 队进入淘汰赛）\n"
            "- 淘汰赛阶段：1/16 决赛(R32) → 1/8 决赛(R16) → 1/4 决赛(QF) → 半决赛(SF) → 三四名(3RD) → 决赛(FINAL)\n"
            "- 共 104 场比赛（小组赛 72 场 + 淘汰赛 32 场）\n"
        ),
        "tools_description": (
            "可用分析能力：\n"
            "1. 小组赛单场预测 — 基于 6 步推理链：实力基线 → 爆冷模式 → 策略性动机 → 第3名出线概率 → 综合概率 → 淘汰赛路径\n"
            "2. 淘汰赛单场预测 — 基于 5 步推理链：小组赛信号 → 特质匹配 → 轮次压力 → 加时/点球决胜 → 综合概率\n"
            "3. 球队综合分析 — 5 维雷达图（攻击力、防守力、中场控制、大赛经验、阵容深度）+ 胜率评估\n"
        ),
        "date_notice": "当前日期：{current_date}",
        "rules": (
            "回答规范：\n"
            "- 使用专业但易懂的语言\n"
            "- 提供数据支撑的分析，避免纯主观判断\n"
            "- 明确标注预测置信度（高/中/低）\n"
            "- 如涉及概率预测，给出具体数值\n"
            "- 在分析末尾附上免责声明：预测仅供参考，实际结果可能不同\n"
            "- 你的思考过程和最终回答必须全部使用中文（简体）\n"
        ),
    },
    "en-US": {
        "role_description": (
            "You are the AI analysis assistant for the 2026 FIFA World Cup. "
            "You specialise in football match analysis and can deliver professional "
            "predictions and insights based on FIFA rankings, team traits, historical "
            "data, and tournament format constraints."
        ),
        "tournament_context": (
            "Tournament Background: 2026 FIFA World Cup (USA / Canada / Mexico)\n"
            "- 48 teams / 12 groups / 4 teams per group\n"
            "- Top 2 + 8 best 3rd-placed teams advance (32 teams in knockout stage)\n"
            "- Knockout rounds: R32 → R16 → QF → SF → 3RD → FINAL\n"
            "- Total 104 matches (72 group stage + 32 knockout)\n"
        ),
        "tools_description": (
            "Available analysis capabilities:\n"
            "1. Group-stage match prediction — 6-step reasoning chain: base strength → upset pattern → "
            "strategic motivation → 3rd-place advancement → probability synthesis → knockout path\n"
            "2. Knockout match prediction — 5-step reasoning chain: group signals → trait matchup → "
            "round pressure → extra-time/penalty → probability synthesis\n"
            "3. Team analysis — 5-dimension radar (attack, defence, midfield control, "
            "tournament experience, squad depth) + win probability assessment\n"
        ),
        "date_notice": "Current date: {current_date}",
        "rules": (
            "Response guidelines:\n"
            "- Use professional yet accessible language\n"
            "- Support analysis with data; avoid purely subjective claims\n"
            "- Clearly state prediction confidence (HIGH / MEDIUM / LOW)\n"
            "- Include specific probability figures when predicting outcomes\n"
            "- Append a disclaimer at the end: predictions are for reference only\n"
            "- Your reasoning and final answer must be in English\n"
        ),
    },
}


# ---------------------------------------------------------------------------
# Analysis prompt templates (group-stage / knockout intros)
# ---------------------------------------------------------------------------

ANALYSIS_PROMPTS: Dict[str, Dict[str, str]] = {
    "zh-CN": {
        "group_analysis_intro": (
            "请基于以下小组赛预测推理链，对比赛 {match_id}（{team1} vs {team2}）进行完整分析。\n\n"
            "要求：\n"
            "1. 严格按照 STEP 0 → STEP 6 的顺序逐步执行推理\n"
            "2. 每个 STEP 必须引用推理链中对应的公式、概率表和修正系数进行计算\n"
            "3. 使用 Markdown 格式输出，每个推理步骤使用二级标题（## Step N）\n"
            "4. 关键数据（概率、排名差、修正系数等）使用加粗或列表展示\n"
            "5. 最终在「## 综合预测」中汇总所有步骤的结果\n"
            "6. 末尾附上免责声明\n\n"
            "推理链模板：\n"
        ),
        "custom_analysis_intro": (
            "请基于以下「轮次差异化策略」推理链，对比赛 {match_id}（{team1} vs {team2}）"
            "进行定制版策略分析。\n\n"
            "要求：\n"
            "1. 首先判断当前轮次（R1/R2/R3），然后按照 STEP 0 → STEP 6 的顺序执行推理\n"
            "2. 每个步骤必须引用推理链中对应的轮次修正因子、爆冷系数和策略权重进行计算\n"
            "3. 在分析开头明确标注本场所采用的策略模式（爆冷猎手/稳定猎手/终局博弈猎手）\n"
            "4. 使用 Markdown 格式输出，每个推理步骤使用二级标题（## Step N）\n"
            "5. 关键数据（轮次修正因子、爆冷系数、MAF、策略信号）使用加粗或列表展示\n"
            "6. 在「## 策略预测总结」中按轮次策略模式汇总推荐比分和策略信号\n"
            "7. 末尾附上免责声明\n"
            "8. **输出精简原则**：每个步骤只展示核心计算过程和结论，"
            "省略推理链中不适用于当前轮次的分支；总输出控制在 3000 字以内\n\n"
            "轮次策略推理链：\n"
        ),
        "knockout_analysis_intro": (
            "请基于以下淘汰赛预测推理链，对比赛 {match_id}（{team1} vs {team2}）进行分析。"
            "严格按照 STEP 1 → STEP 5 的顺序执行推理，输出 JSON 格式的完整分析结果。\n\n"
            "推理链模板：\n"
        ),
    },
    "en-US": {
        "group_analysis_intro": (
            "Analyse match {match_id} ({team1} vs {team2}) using the group-stage "
            "prediction reasoning chain below.\n\n"
            "Requirements:\n"
            "1. Follow STEP 0 → STEP 6 strictly in order\n"
            "2. Each STEP must reference the corresponding formulas, probability tables "
            "and correction factors from the reasoning chain\n"
            "3. Use Markdown format with level-2 headings for each step (## Step N)\n"
            "4. Key data (probabilities, rank diff, correction factors) in bold or lists\n"
            "5. Summarise all steps in a final '## Final Prediction' section\n"
            "6. Append a disclaimer at the end\n\n"
            "Reasoning chain template:\n"
        ),
        "custom_analysis_intro": (
            "Analyse match {match_id} ({team1} vs {team2}) using the "
            "\"Round-Differentiated Strategy\" reasoning chain below.\n\n"
            "Requirements:\n"
            "1. First determine the current round (R1/R2/R3), then follow "
            "STEP 0 → STEP 6 strictly in order\n"
            "2. Each step must reference the corresponding round correction factors, "
            "upset multipliers and strategy weights from the reasoning chain\n"
            "3. Clearly state the strategy mode at the beginning "
            "(Upset Hunter / Stability Hunter / Endgame Hunter)\n"
            "4. Use Markdown format with level-2 headings for each step (## Step N)\n"
            "5. Key data (round correction, upset multiplier, MAF, strategy signals) "
            "in bold or lists\n"
            "6. Summarise recommended scores and strategy signals in a "
            "'## Strategic Prediction Summary' section\n"
            "7. Append a disclaimer at the end\n"
            "8. **Brevity principle**: Only show core calculations and conclusions "
            "per step; omit branches not applicable to the current round. "
            "Keep total output under 3000 words.\n\n"
            "Round strategy reasoning chain:\n"
        ),
        "knockout_analysis_intro": (
            "Analyse match {match_id} ({team1} vs {team2}) using the knockout-stage "
            "prediction reasoning chain below. Follow STEP 1 → STEP 5 strictly and "
            "output the complete analysis as JSON.\n\n"
            "Reasoning chain template:\n"
        ),
    },
}
