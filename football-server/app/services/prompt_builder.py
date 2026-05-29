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

from app.schemas.ai_schema import ChatMessageItem, MatchAnalysisRequest, SkillInfo

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
# Skill registry
# ---------------------------------------------------------------------------

_SKILL_REGISTRY: Dict[str, Dict] = {
    "group_stage_predict": {
        "loader": _get_group_stage_skill,
        "name": "Group Stage Prediction",
        "name_zh": "小组赛单场预测",
        "description": "6-step reasoning chain for group stage matches",
        "description_zh": "基于6步推理链的小组赛单场胜负预测",
        "applicable_stages": ["group"],
    },
    "knockout_stage_predict": {
        "loader": _get_knockout_stage_skill,
        "name": "Knockout Stage Prediction",
        "name_zh": "淘汰赛单场预测",
        "description": "5-step reasoning chain for knockout matches",
        "description_zh": "基于5步推理链的淘汰赛单场预测（含加时/点球）",
        "applicable_stages": ["R32", "R16", "QF", "SF", "3rd", "F"],
    },
}


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

    # ── Skill registry helpers ────────────────────────────────────────────

    @staticmethod
    def resolve_skill_id(skill_id: str | None, stage: str) -> str:
        """Resolve the effective skill_id from an explicit override or stage.

        Parameters
        ----------
        skill_id:
            Explicit skill identifier, or ``None`` to auto-detect.
        stage:
            Tournament stage (e.g. ``"group"``, ``"R16"``).

        Returns
        -------
        str
            The resolved skill_id (defaults to ``"group_stage_predict"``).
        """
        if skill_id is not None:
            return skill_id

        for sid, meta in _SKILL_REGISTRY.items():
            if stage in meta.get("applicable_stages", []):
                return sid

        return "group_stage_predict"

    @staticmethod
    def get_available_skills() -> List[SkillInfo]:
        """Return metadata for all registered skills.

        Returns
        -------
        list[SkillInfo]
            Skill descriptors suitable for API responses.
        """
        return [
            SkillInfo(
                skill_id=sid,
                name=meta["name"],
                name_zh=meta["name_zh"],
                description=meta["description"],
                description_zh=meta["description_zh"],
                applicable_stages=meta["applicable_stages"],
            )
            for sid, meta in _SKILL_REGISTRY.items()
        ]

    @staticmethod
    def build_skill_prompt(
        request: MatchAnalysisRequest,
    ) -> List[Dict[str, str]]:
        """Build an OpenAI-compatible message list for a skill-driven analysis.

        The pipeline is:
        1. Resolve the target skill via :meth:`resolve_skill_id`.
        2. Load the skill reasoning-chain content from the registry.
        3. Build a system prompt combining the AI role and the reasoning chain.
        4. Build a user message with the formatted match context and an
           analysis instruction.
        5. Return ``[system_message, user_message]``.

        Parameters
        ----------
        request:
            The structured match analysis request.

        Returns
        -------
        list[dict]
            Two-element message list ready for the chat API.
        """
        resolved_id = PromptBuilder.resolve_skill_id(request.skill_id, request.stage)
        meta = _SKILL_REGISTRY.get(resolved_id)

        # Load skill reasoning chain; fall back to empty string on failure
        skill_content = ""
        if meta is not None:
            try:
                skill_content = meta["loader"]()
            except Exception:
                logger.exception("Failed to load skill: %s", resolved_id)
        else:
            logger.warning("Unknown skill_id resolved: %s", resolved_id)

        lang = request.lang if request.lang in ("zh-CN", "en-US") else "zh-CN"
        fragments = _SYSTEM_FRAGMENTS.get(lang, _SYSTEM_FRAGMENTS["zh-CN"])

        # System message: role + tournament context + skill reasoning chain
        current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        system_parts = [
            fragments["role_description"],
            "",
            fragments["tournament_context"],
            "",
            fragments["date_notice"].format(current_date=current_date),
        ]
        if skill_content:
            system_parts.extend([
                "",
                "---",
                "推理链 / Reasoning Chain:" if lang == "zh-CN" else "---\nReasoning Chain:",
                "",
                skill_content,
            ])
        system_parts.append("")
        system_parts.append(fragments["rules"])

        system_content = "\n".join(system_parts)

        # User message: formatted match context + analysis instruction
        match_context = PromptBuilder._format_match_context(request)

        if lang == "zh-CN":
            instruction = (
                "请根据以上比赛上下文，严格按照推理链中的步骤进行完整分析。\n"
                "输出要求：\n"
                "1. 使用 Markdown 格式输出完整的分析结果\n"
                "2. 每个推理步骤使用二级标题（## Step N）\n"
                "3. 综合预测结论使用独立的二级标题（## 综合预测）\n"
                "4. 关键数据使用加粗或列表展示\n"
                "5. 在末尾附上免责声明"
            )
        else:
            instruction = (
                "Based on the match context above, follow the reasoning chain "
                "steps strictly to produce a complete analysis.\n"
                "Output requirements:\n"
                "1. Use Markdown format for the entire analysis\n"
                "2. Each reasoning step as a level-2 heading (## Step N)\n"
                "3. Final prediction as a separate level-2 heading (## Final Prediction)\n"
                "4. Key data presented in bold or bullet lists\n"
                "5. Append a disclaimer at the end"
            )

        user_content = match_context + "\n\n" + instruction

        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ]

    @staticmethod
    def _format_match_context(request: MatchAnalysisRequest) -> str:
        """Format structured match data into a human-readable analysis context.

        Parameters
        ----------
        request:
            The match analysis request with team, score, and event data.

        Returns
        -------
        str
            Formatted context text suitable for inclusion in an AI prompt.
        """
        lang = request.lang if request.lang in ("zh-CN", "en-US") else "zh-CN"
        home = request.home_team
        away = request.away_team

        if lang == "zh-CN":
            parts: list[str] = [
                f"=== 比赛上下文 ===",
                f"比赛ID: {request.match_id}",
                f"主队: {home.flag} {home.name_zh} ({home.name}) [{home.code}]",
                f"客队: {away.flag} {away.name_zh} ({away.name}) [{away.code}]",
            ]

            # Stage context
            if request.stage == "group":
                stage_label = "小组赛"
                if request.group_label:
                    stage_label += f" {request.group_label}组"
                if request.round:
                    stage_label += f" 第{request.round}轮"
                parts.append(f"阶段: {stage_label}")
            else:
                round_label = request.round or request.stage
                parts.append(f"阶段: 淘汰赛 - {round_label}")

            # Match status
            status_map: dict[str, str] = {
                "upcoming": "未开始",
                "live": "进行中",
                "finished": "已结束",
            }
            parts.append(f"状态: {status_map.get(request.status, request.status)}")

            # Score
            if request.home_score is not None and request.away_score is not None:
                parts.append(
                    f"比分: {home.name_zh} {request.home_score} - "
                    f"{request.away_score} {away.name_zh}"
                )

            # Match day
            if request.match_day is not None:
                parts.append(f"比赛日: 第{request.match_day}天")
        else:
            parts = [
                "=== Match Context ===",
                f"Match ID: {request.match_id}",
                f"Home: {home.flag} {home.name} [{home.code}]",
                f"Away: {away.flag} {away.name} [{away.code}]",
            ]

            if request.stage == "group":
                stage_label = "Group Stage"
                if request.group_label:
                    stage_label += f" Group {request.group_label}"
                if request.round:
                    stage_label += f" Round {request.round}"
                parts.append(f"Stage: {stage_label}")
            else:
                round_label = request.round or request.stage
                parts.append(f"Stage: Knockout - {round_label}")

            parts.append(f"Status: {request.status}")

            if request.home_score is not None and request.away_score is not None:
                parts.append(
                    f"Score: {home.name} {request.home_score} - "
                    f"{request.away_score} {away.name}"
                )

            if request.match_day is not None:
                parts.append(f"Match Day: {request.match_day}")

        # Events timeline
        if request.events:
            event_lines: list[str] = []
            for evt in request.events:
                team = home if evt.team_side == "home" else away
                side_label = team.name_zh if lang == "zh-CN" else team.name
                player = f" ({evt.player_name})" if evt.player_name else ""
                event_lines.append(
                    f"  [{evt.minute}'] {evt.event_type} - {side_label}{player}"
                )

            header = "比赛事件:" if lang == "zh-CN" else "Match Events:"
            parts.append(header)
            parts.extend(event_lines)

        return "\n".join(parts)
