"""AI prompt builder — constructs system prompts and analysis prompts.

Reads the skill definition files from ``skills/`` at module load time and
exposes methods to build OpenAI-compatible message lists for different
chat and analysis scenarios.  All user-facing text is bilingual (zh-CN / en-US).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Literal

from app.schemas.ai_schema import ChatMessageItem

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Skill file loading
# ---------------------------------------------------------------------------

_SKILLS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "skills"


def _read_skill(filename: str) -> str:
    """Read a skill markdown file from the ``skills/`` directory."""
    path = _SKILLS_DIR / filename
    if not path.exists():
        logger.warning("Skill file not found: %s", path)
        return ""
    return path.read_text(encoding="utf-8")


# Lazy-loaded skill content
_GROUP_STAGE_SKILL: str | None = None
_KNOCKOUT_STAGE_SKILL: str | None = None


def _get_group_stage_skill() -> str:
    global _GROUP_STAGE_SKILL  # noqa: PLW0603
    if _GROUP_STAGE_SKILL is None:
        _GROUP_STAGE_SKILL = _read_skill("group_stage_predict.md")
    return _GROUP_STAGE_SKILL


def _get_knockout_stage_skill() -> str:
    global _KNOCKOUT_STAGE_SKILL  # noqa: PLW0603
    if _KNOCKOUT_STAGE_SKILL is None:
        _KNOCKOUT_STAGE_SKILL = _read_skill("knockout_stage_predict.md")
    return _KNOCKOUT_STAGE_SKILL


# ---------------------------------------------------------------------------
# Language-aware text fragments
# ---------------------------------------------------------------------------

_SYSTEM_FRAGMENTS: Dict[str, Dict[str, str]] = {
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
        ),
    },
}

_ANALYSIS_PROMPTS: Dict[str, Dict[str, str]] = {
    "zh-CN": {
        "group_analysis_intro": (
            "请基于以下小组赛预测推理链，对比赛 {match_id}（{team1} vs {team2}）进行分析。"
            "严格按照 STEP 1 → STEP 6 的顺序执行推理，输出 JSON 格式的完整分析结果。\n\n"
            "推理链模板：\n"
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
            "prediction reasoning chain below. Follow STEP 1 → STEP 6 strictly and "
            "output the complete analysis as JSON.\n\n"
            "Reasoning chain template:\n"
        ),
        "knockout_analysis_intro": (
            "Analyse match {match_id} ({team1} vs {team2}) using the knockout-stage "
            "prediction reasoning chain below. Follow STEP 1 → STEP 5 strictly and "
            "output the complete analysis as JSON.\n\n"
            "Reasoning chain template:\n"
        ),
    },
}


# ---------------------------------------------------------------------------
# PromptBuilder
# ---------------------------------------------------------------------------


class PromptBuilder:
    """Constructs AI prompts for chat, match analysis, and knockout predictions.

    All public methods return ``list[dict]`` — an OpenAI-compatible message list
    where each element has ``role`` and ``content`` keys.
    """

    # ── System prompt ──────────────────────────────────────────────────────

    @staticmethod
    def build_system_prompt(
        lang: Literal["zh-CN", "en-US"] = "zh-CN",
    ) -> List[Dict[str, str]]:
        """Build the system prompt message with tournament context and rules.

        Parameters
        ----------
        lang:
            Language for the system prompt.

        Returns
        -------
        list[dict]
            A single-element list containing the system message.
        """
        fragments = _SYSTEM_FRAGMENTS.get(lang, _SYSTEM_FRAGMENTS["zh-CN"])
        current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        content = "\n".join(
            [
                fragments["role_description"],
                "",
                fragments["tournament_context"],
                fragments["tools_description"],
                "",
                fragments["date_notice"].format(current_date=current_date),
                "",
                fragments["rules"],
            ]
        )

        return [{"role": "system", "content": content}]

    # ── Group-stage match analysis prompt ──────────────────────────────────

    @staticmethod
    def build_match_analysis_prompt(
        match_id: str,
        team1: str,
        team2: str,
        *,
        lang: Literal["zh-CN", "en-US"] = "zh-CN",
    ) -> List[Dict[str, str]]:
        """Build a group-stage match analysis prompt based on the 6-step reasoning chain.

        Parameters
        ----------
        match_id:
            Match identifier (e.g. ``"A_M1"``).
        team1, team2:
            Team names for the home and away sides.
        lang:
            Language for the prompt.

        Returns
        -------
        list[dict]
            System message + user message containing the full reasoning chain.
        """
        system_messages = PromptBuilder.build_system_prompt(lang)
        skill_content = _get_group_stage_skill()
        prompts = _ANALYSIS_PROMPTS.get(lang, _ANALYSIS_PROMPTS["zh-CN"])

        user_content = prompts["group_analysis_intro"].format(
            match_id=match_id,
            team1=team1,
            team2=team2,
        )
        user_content += skill_content

        return system_messages + [{"role": "user", "content": user_content}]

    # ── Knockout match prediction prompt ───────────────────────────────────

    @staticmethod
    def build_knockout_prompt(
        match_id: str,
        team1: str,
        team2: str,
        *,
        lang: Literal["zh-CN", "en-US"] = "zh-CN",
    ) -> List[Dict[str, str]]:
        """Build a knockout-stage match prediction prompt based on the 5-step reasoning chain.

        Parameters
        ----------
        match_id:
            Match identifier (e.g. ``"R32_01"``).
        team1, team2:
            Team names for the home and away sides.
        lang:
            Language for the prompt.

        Returns
        -------
        list[dict]
            System message + user message containing the full reasoning chain.
        """
        system_messages = PromptBuilder.build_system_prompt(lang)
        skill_content = _get_knockout_stage_skill()
        prompts = _ANALYSIS_PROMPTS.get(lang, _ANALYSIS_PROMPTS["zh-CN"])

        user_content = prompts["knockout_analysis_intro"].format(
            match_id=match_id,
            team1=team1,
            team2=team2,
        )
        user_content += skill_content

        return system_messages + [{"role": "user", "content": user_content}]

    # ── Chat context formatter ─────────────────────────────────────────────

    @staticmethod
    def build_chat_context(
        messages: List[ChatMessageItem],
    ) -> List[Dict[str, str]]:
        """Convert a list of :class:`ChatMessageItem` into the OpenAI message format.

        Parameters
        ----------
        messages:
            Chat history from the client request.

        Returns
        -------
        list[dict]
            Messages formatted as ``[{"role": ..., "content": ...}, ...]``.
        """
        return [{"role": msg.role, "content": msg.content} for msg in messages]
