"""Championship prediction instruction templates.

Contains the bilingual (zh-CN / en-US) detailed championship prediction
instructions used in the championship analysis prompt.  Extracted from
``prompt_builder.py`` to keep that module under the 600-line hard-limit.

Templates use ``{simulation_count}`` placeholder so the caller can inject
a user-configurable Monte Carlo run count.
"""

from __future__ import annotations

from typing import Dict


def _build_zh_instruction(simulation_count: int) -> str:
    """Build the zh-CN championship instruction with the given simulation count."""
    count_str = f"{simulation_count:,}"
    return (
        f"> ⚠️ **强制要求**：本次分析必须模拟 **{count_str} 次**（用户指定），"
        "所有输出中的模拟次数必须与此数字一致，不得使用其他数值。\n\n"
        "## 冠亚军预测任务\n\n"
        "请对 2026 年 FIFA 世界杯进行完整的冠亚军预测分析。你必须严格按照以下流程执行：\n\n"
        "### 第一阶段：小组赛模拟\n"
        "1. 基于每支球队的真实 FIFA 排名、德转身价、近期状态，评估各小组的实力对比\n"
        "2. 考虑小组赛的赛程时间线，注意各组第三轮的开球时间差异可能导致信息不对称和控分行为\n"
        "3. 给出每个小组最可能的前两名和进入「最佳第三名」的球队\n\n"
        "### 第二阶段：淘汰赛落位与蒙特卡洛模拟\n"
        "1. 根据小组赛结果，按照 FIFA 官方对阵表将 32 支球队落位\n"
        f"2. 模拟 **{count_str} 次** 完整的淘汰赛过程，从 1/16 决赛一直到决赛\n"
        "3. 在每次模拟中，必须遵循真实的赛程时间线（小组赛 → 32强 → 16强 → 8强 → 半决赛 → 决赛）\n"
        "4. 严格应用策略文件中的七大核心预测策略：\n"
        "   - 第三名逆袭惩罚机制（Underdog Pruning）\n"
        "   - 纸面实力导向（Seed Squad Dominance）\n"
        "   - 同组分流排除（Bracket Collision Detection）\n"
        "   - 死亡之组第三名特赦（Powerhouse Amnesty）\n"
        "   - 第三名落位蒙特卡洛矩阵（Dynamic 3rd-Placers Matrix）\n"
        "   - 杯赛韧性加权修正（Tournament Grit Factor）\n"
        "   - 时间序列博弈（Chronological Game Theory）\n\n"
        "### 第三阶段：结果输出\n"
        "请按照以下格式输出最终的冠亚军预测结果：\n\n"
        "#### 🏆 决赛名单 TOP 20（按概率从高到低排列）\n\n"
        "对每个决赛组合，输出：\n"
        "- **决赛对阵**：球队 A vs 球队 B\n"
        f"- **出现概率**：X.X%（基于 {count_str} 次模拟）\n"
        "- **入选原因**：简要说明这两支球队各自从小组赛到决赛的晋级路径、关键策略因素\n\n"
        "#### 📊 核心发现\n"
        "- 最可能的冠军及原因\n"
        "- 最大黑马分析\n"
        "- 死亡之组对淘汰赛格局的影响\n\n"
        "#### ⚠️ 数据约束\n"
        "- 所有概率数据必须基于模拟计算，不得凭空捏造\n"
        "- 不得出现同一小组两支球队同时进入决赛的情况（违反策略三）\n"
        "- 概率之和必须合理（TOP 20 的概率总和应在合理范围内）\n"
        "- 不得出现明显不合理的晋级路径（如 FIFA 排名 100+ 的球队进入决赛）\n\n"
        "在末尾附上免责声明：以上预测基于模拟分析，仅供参考。\n"
    )


def _build_en_instruction(simulation_count: int) -> str:
    """Build the en-US championship instruction with the given simulation count."""
    count_str = f"{simulation_count:,}"
    return (
        f"> ⚠️ **MANDATORY**: This analysis MUST simulate exactly **{count_str}** runs "
        "(user-specified). All output references to simulation count MUST match this number exactly.\n\n"
        "## Championship Prediction Task\n\n"
        "Please conduct a complete champion and runner-up prediction analysis for the "
        "2026 FIFA World Cup. Follow this process strictly:\n\n"
        "### Phase 1: Group Stage Simulation\n"
        "1. Evaluate each group's strength based on real FIFA rankings, Transfermarkt market values, "
        "and recent form\n"
        "2. Consider the group stage schedule timeline, noting that kickoff time differences "
        "in matchday 3 may cause information asymmetry and strategic tanking\n"
        "3. Predict the most likely top 2 and 'best third-placed' teams for each group\n\n"
        "### Phase 2: Knockout Placement & Monte Carlo Simulation\n"
        "1. Place the 32 qualified teams according to the official FIFA bracket\n"
        f"2. Simulate **{count_str}** complete knockout runs from R32 through the Final\n"
        "3. Each simulation must follow the real tournament timeline "
        "(Group Stage → R32 → R16 → QF → SF → Final)\n"
        "4. Strictly apply the 7 core prediction strategies from the strategy file:\n"
        "   - Underdog Pruning\n"
        "   - Seed Squad Dominance\n"
        "   - Bracket Collision Detection\n"
        "   - Powerhouse Amnesty\n"
        "   - Dynamic 3rd-Placers Matrix\n"
        "   - Tournament Grit Factor\n"
        "   - Chronological Game Theory\n\n"
        "### Phase 3: Results Output\n"
        "Output the final champion/runner-up predictions in this format:\n\n"
        "#### 🏆 Final Matchup TOP 20 (Ranked by Probability)\n\n"
        "For each final combination:\n"
        "- **Final Matchup**: Team A vs Team B\n"
        f"- **Probability**: X.X% (based on {count_str} simulations)\n"
        "- **Reasoning**: Brief explanation of each team's path from group stage to final, "
        "key strategic factors\n\n"
        "#### 📊 Key Findings\n"
        "- Most likely champion and reasoning\n"
        "- Biggest dark horse analysis\n"
        "- Impact of groups of death on the knockout bracket\n\n"
        "#### ⚠️ Data Constraints\n"
        "- All probability data must be based on simulated calculations, not fabricated\n"
        "- Two teams from the same group may NOT both reach the final (Strategy 3)\n"
        "- Probabilities must sum to reasonable totals (TOP 20 should have a plausible combined probability)\n"
        "- No implausible advancement paths (e.g., FIFA rank 100+ teams reaching the final)\n\n"
        "Append a disclaimer: The above predictions are based on simulation analysis and are for reference only.\n"
    )


def get_championship_instruction(lang: str, simulation_count: int) -> str:
    """Return the championship instruction string for the given language and sim count."""
    if lang == "en-US":
        return _build_en_instruction(simulation_count)
    return _build_zh_instruction(simulation_count)
