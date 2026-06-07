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

from app.schemas.ai_schema import (
    ChampionshipAnalysisRequest,
    ChatMessageItem,
    MatchAnalysisRequest,
    SkillInfo,
)
from app.services.prompts.championship_prompts import get_championship_instruction
from app.services.prompts.system_prompts import ANALYSIS_PROMPTS, SYSTEM_FRAGMENTS

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
_GROUP_STAGE_ROUND_STRATEGY_SKILL: str | None = None
_KNOCKOUT_STAGE_SKILL: str | None = None
_CHAMPIONSHIP_SKILL: str | None = None


def _get_group_stage_skill() -> str:
    global _GROUP_STAGE_SKILL  # noqa: PLW0603
    if _GROUP_STAGE_SKILL is None:
        _GROUP_STAGE_SKILL = _read_skill("group_stage_predict.md")
    return _GROUP_STAGE_SKILL


def _get_group_stage_round_strategy_skill() -> str:
    global _GROUP_STAGE_ROUND_STRATEGY_SKILL  # noqa: PLW0603
    if _GROUP_STAGE_ROUND_STRATEGY_SKILL is None:
        _GROUP_STAGE_ROUND_STRATEGY_SKILL = _read_skill(
            "group_stage_round_strategy.md"
        )
    return _GROUP_STAGE_ROUND_STRATEGY_SKILL


def _get_knockout_stage_skill() -> str:
    global _KNOCKOUT_STAGE_SKILL  # noqa: PLW0603
    if _KNOCKOUT_STAGE_SKILL is None:
        _KNOCKOUT_STAGE_SKILL = _read_skill("knockout_stage_predict.md")
    return _KNOCKOUT_STAGE_SKILL


def _get_championship_skill() -> str:
    global _CHAMPIONSHIP_SKILL  # noqa: PLW0603
    if _CHAMPIONSHIP_SKILL is None:
        _CHAMPIONSHIP_SKILL = _read_skill("冠亚军分析.md")
    return _CHAMPIONSHIP_SKILL


# ---------------------------------------------------------------------------
# Skill registry
# ---------------------------------------------------------------------------

_SKILL_REGISTRY: Dict[str, Dict] = {
    "group_stage_predict": {
        "loader": _get_group_stage_skill,
        "filename": "group_stage_predict.md",
        "name": "Group Stage Prediction",
        "name_zh": "小组赛单场预测",
        "description": "6-step reasoning chain for group stage matches",
        "description_zh": "基于6步推理链的小组赛单场胜负预测",
        "applicable_stages": ["group"],
    },
    "group_stage_round_strategy": {
        "loader": _get_group_stage_round_strategy_skill,
        "filename": "group_stage_round_strategy.md",
        "name": "Group Stage Round Strategy",
        "name_zh": "小组赛轮次策略预测",
        "description": "Round-differentiated strategy: R1 upset/high-scoring + R2 stability + R3 rotation/tacit draw",
        "description_zh": "轮次差异化策略：R1爆冷/大球 + R2稳定正向 + R3放水/默契球",
        "applicable_stages": ["group"],
    },
    "knockout_stage_predict": {
        "loader": _get_knockout_stage_skill,
        "filename": "knockout_stage_predict.md",
        "name": "Knockout Stage Prediction",
        "name_zh": "淘汰赛单场预测",
        "description": "5-step reasoning chain for knockout matches",
        "description_zh": "基于5步推理链的淘汰赛单场预测（含加时/点球）",
        "applicable_stages": ["R32", "R16", "QF", "SF", "3rd", "F"],
    },
    "championship_predict": {
        "loader": _get_championship_skill,
        "filename": "冠亚军分析.md",
        "name": "Championship Prediction",
        "name_zh": "冠亚军预测",
        "description": "Monte Carlo simulation for champion & runner-up prediction",
        "description_zh": "基于蒙特卡洛模拟的冠亚军预测分析（可自定义推演次数）",
        "applicable_stages": ["tournament"],
    },
}

# Reverse mapping: filename → registry key (for backward-compatible lookup)
_FILENAME_TO_SKILL_ID: Dict[str, str] = {
    meta["filename"]: sid for sid, meta in _SKILL_REGISTRY.items()
}


# ---------------------------------------------------------------------------
# Prompt constants are imported from app.services.prompts:
#   SYSTEM_FRAGMENTS  -> prompts.system_prompts
#   ANALYSIS_PROMPTS  -> prompts.system_prompts
#   get_championship_instruction -> prompts.championship_prompts
# ---------------------------------------------------------------------------


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
        fragments = SYSTEM_FRAGMENTS.get(lang, SYSTEM_FRAGMENTS["zh-CN"])
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
        prompts = ANALYSIS_PROMPTS.get(lang, ANALYSIS_PROMPTS["zh-CN"])

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
        prompts = ANALYSIS_PROMPTS.get(lang, ANALYSIS_PROMPTS["zh-CN"])

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
        """Dynamically scan the ``skills/`` directory and return all ``*.md`` files.

        Each file becomes a selectable skill.  Registry metadata (bilingual
        names, descriptions, stages) is used when available; otherwise sensible
        defaults are derived from the filename.

        Returns
        -------
        list[SkillInfo]
            Skill descriptors suitable for API responses.
        """
        skills: List[SkillInfo] = []

        for path in sorted(_SKILLS_DIR.glob("*.md")):
            if path.name == "README.md":
                continue

            filename = path.name  # e.g. "冠亚军分析.md"
            stem = path.stem  # e.g. "冠亚军分析"

            # Look up enriched metadata from the registry
            sid = _FILENAME_TO_SKILL_ID.get(filename)
            if sid is not None:
                meta = _SKILL_REGISTRY[sid]
                skills.append(
                    SkillInfo(
                        skill_id=filename,
                        name=stem,
                        name_zh=stem,
                        description=meta["description"],
                        description_zh=meta["description_zh"],
                        applicable_stages=meta["applicable_stages"],
                    )
                )
            else:
                # No registry entry — use filename as display text
                skills.append(
                    SkillInfo(
                        skill_id=filename,
                        name=stem,
                        name_zh=stem,
                        description=f"Skill file: {filename}",
                        description_zh=f"技能文件: {filename}",
                        applicable_stages=["tournament"],
                    )
                )

        return skills

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
        fragments = SYSTEM_FRAGMENTS.get(lang, SYSTEM_FRAGMENTS["zh-CN"])

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

    # ── Championship prediction prompt ─────────────────────────────────────

    @staticmethod
    def build_championship_prompt(
        request: ChampionshipAnalysisRequest,
    ) -> List[Dict[str, str]]:
        """Build an OpenAI-compatible message list for championship prediction.

        Combines the system role prompt, the championship strategy skill content,
        and the detailed championship analysis instruction into a two-message
        list suitable for the Deepseek streaming API.

        Parameters
        ----------
        request:
            The championship analysis request with language preference.

        Returns
        -------
        list[dict]
            Two-element message list ``[system, user]``.
        """
        raw_id = request.skill_id or "冠亚军分析.md"

        # Load skill content — accept filenames or legacy registry keys
        skill_content = ""
        sid = _FILENAME_TO_SKILL_ID.get(raw_id)

        if sid is not None:
            # raw_id is a known filename → use registry loader
            try:
                skill_content = _SKILL_REGISTRY[sid]["loader"]()
            except Exception:
                logger.exception("Failed to load skill: %s", raw_id)
        elif raw_id in _SKILL_REGISTRY:
            # Legacy registry key (backward compat)
            try:
                skill_content = _SKILL_REGISTRY[raw_id]["loader"]()
            except Exception:
                logger.exception("Failed to load skill: %s", raw_id)
        else:
            # Unknown identifier — try reading as a raw filename
            skill_content = _read_skill(raw_id)
            if not skill_content:
                logger.warning("Unknown championship skill_id: %s", raw_id)

        lang = request.lang if request.lang in ("zh-CN", "en-US") else "zh-CN"
        fragments = SYSTEM_FRAGMENTS.get(lang, SYSTEM_FRAGMENTS["zh-CN"])

        # System message: role + tournament context + championship strategies
        current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        system_parts: list[str] = [
            fragments["role_description"],
            "",
            fragments["tournament_context"],
            "",
            fragments["date_notice"].format(current_date=current_date),
        ]

        if skill_content:
            # Substitute dynamic placeholders in skill content
            sim_count_fmt = f"{request.simulation_count:,}"
            skill_content = skill_content.replace(
                "{simulation_count}", sim_count_fmt
            )
            system_parts.extend([
                "",
                "---",
                (
                    "冠亚军预测策略库 / Championship Prediction Strategies:"
                    if lang == "zh-CN"
                    else "---\nChampionship Prediction Strategies:"
                ),
                "",
                skill_content,
            ])

        system_parts.append("")
        system_parts.append(fragments["rules"])

        system_content = "\n".join(system_parts)

        # User message: championship analysis instruction
        user_content = get_championship_instruction(lang, request.simulation_count)

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
