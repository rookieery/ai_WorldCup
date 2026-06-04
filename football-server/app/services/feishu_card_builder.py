"""Feishu interactive card message builder.

Pure-function module — no I/O, no side effects.  Every function returns
a dict that conforms to the Feishu Interactive Card JSON schema and can
be passed directly to ``FeishuClient.send_card_message`` or ``reply_message``.

All user-visible strings are bilingual (``zh-CN`` / ``en-US``).
"""

from __future__ import annotations

from typing import Any, Dict, List

# ── Shared helpers ───────────────────────────────────────────────────────────


def _card_config() -> Dict[str, Any]:
    """Return the default card config block."""
    return {"wide_screen_mode": True, "enable_forward": True}


def _header(
    title: str,
    *,
    template: str = "turquoise",
) -> Dict[str, Any]:
    """Build a card header with a plain-text title and colour template."""
    return {
        "title": {"tag": "plain_text", "content": title},
        "template": template,
    }


def _markdown(content: str) -> Dict[str, Any]:
    """Build a single markdown element."""
    return {"tag": "markdown", "content": content}


def _divider() -> Dict[str, Any]:
    """Build a horizontal divider element."""
    return {"tag": "hr"}


def _team_display(team: Dict[str, Any], lang: str) -> str:
    """Return ``'🇧🇷 Brazil'`` style display string for a team dict."""
    flag = team.get("flag", "")
    name = team.get("name_zh", "") if lang == "zh-CN" else team.get("name", "")
    return f"{flag} {name}" if flag else name


# ── Match event cards (Phase 1 — push) ──────────────────────────────────────

I18N = {
    "zh-CN": {
        "match_start": "⚽ 比赛开始！",
        "score_update": "⚽ 进球！",
        "match_end": "🏆 比赛结束",
        "vs": " vs ",
        "score_separator": " : ",
        "venue": "🏟 {venue}",
        "stage": "📋 {stage}",
        "final_score": "最终比分",
        "current_score": "当前比分",
        "kickoff_time": "开赛时间：{time}",
        "today_matches": "📅 今日赛程",
        "today_matches_empty": "今日暂无比赛",
        "ai_analysis": "🤖 AI 分析",
        "ai_query": "查询",
        "error_title": "⚠️ 出错了",
        "no_data": "暂无数据",
    },
    "en-US": {
        "match_start": "⚽ Match Kickoff!",
        "score_update": "⚽ Goal!",
        "match_end": "🏆 Match Result",
        "vs": " vs ",
        "score_separator": " - ",
        "current_score": "Current Score",
        "final_score": "Final Score",
        "venue": "🏟 {venue}",
        "stage": "📋 {stage}",
        "kickoff_time": "Kickoff: {time}",
        "today_matches": "📅 Today's Matches",
        "today_matches_empty": "No matches today",
        "ai_analysis": "🤖 AI Analysis",
        "ai_query": "Query",
        "error_title": "⚠️ Error",
        "no_data": "No data available",
    },
}


def _t(lang: str) -> Dict[str, str]:
    """Return the i18n lookup dict for *lang*."""
    return I18N.get(lang, I18N["en-US"])


def build_match_start_card(
    match_data: Dict[str, Any],
    *,
    lang: str = "zh-CN",
) -> Dict[str, Any]:
    """Build a 'match kicked off' notification card.

    ``match_data`` keys expected: ``home_team``, ``away_team``, ``venue``,
    ``stage``, ``kickoff`` (optional time string).
    """
    t = _t(lang)
    home = match_data.get("home_team", {})
    away = match_data.get("away_team", {})
    venue_name = (match_data.get("venue") or {}).get("name", "")
    stage = match_data.get("stage", "")

    elements: List[Dict[str, Any]] = [
        _markdown(
            f"**{_team_display(home, lang)}**{t['vs']}**{_team_display(away, lang)}**"
        ),
    ]

    if venue_name:
        elements.append(_markdown(t["venue"].format(venue=venue_name)))
    if stage:
        elements.append(_markdown(t["stage"].format(stage=stage)))

    return {
        "config": _card_config(),
        "header": _header(t["match_start"], template="green"),
        "elements": elements,
    }


def build_score_update_card(
    match_data: Dict[str, Any],
    *,
    home_score: int = 0,
    away_score: int = 0,
    lang: str = "zh-CN",
) -> Dict[str, Any]:
    """Build a 'goal / score update' notification card."""
    t = _t(lang)
    home = match_data.get("home_team", {})
    away = match_data.get("away_team", {})

    elements: List[Dict[str, Any]] = [
        _markdown(
            f"**{_team_display(home, lang)}**"
            f" {home_score}{t['score_separator']}{away_score} "
            f"**{_team_display(away, lang)}**"
        ),
        _markdown(f"*{t['current_score']}*"),
    ]

    return {
        "config": _card_config(),
        "header": _header(t["score_update"], template="orange"),
        "elements": elements,
    }


def build_match_end_card(
    match_data: Dict[str, Any],
    *,
    home_score: int = 0,
    away_score: int = 0,
    lang: str = "zh-CN",
) -> Dict[str, Any]:
    """Build a 'match finished' notification card."""
    t = _t(lang)
    home = match_data.get("home_team", {})
    away = match_data.get("away_team", {})
    venue_name = (match_data.get("venue") or {}).get("name", "")
    stage = match_data.get("stage", "")

    elements: List[Dict[str, Any]] = [
        _markdown(
            f"**{_team_display(home, lang)}**"
            f" {home_score}{t['score_separator']}{away_score} "
            f"**{_team_display(away, lang)}**"
        ),
        _markdown(f"**{t['final_score']}**"),
    ]

    if venue_name:
        elements.append(_markdown(t["venue"].format(venue=venue_name)))
    if stage:
        elements.append(_markdown(t["stage"].format(stage=stage)))

    return {
        "config": _card_config(),
        "header": _header(t["match_end"], template="blue"),
        "elements": elements,
    }


# ── Bot query cards (Phase 3 — interactive) ────────────────────────────────


def build_today_matches_card(
    matches: List[Dict[str, Any]],
    *,
    lang: str = "zh-CN",
) -> Dict[str, Any]:
    """Build a card listing today's matches with times and scores.

    Each match dict should contain ``home_team``, ``away_team``,
    ``home_score``, ``away_score``, ``status``, and optionally
    ``host_time`` / ``kickoff_utc``.
    """
    t = _t(lang)

    if not matches:
        return {
            "config": _card_config(),
            "header": _header(t["today_matches"], template="purple"),
            "elements": [_markdown(t["today_matches_empty"])],
        }

    elements: List[Dict[str, Any]] = []
    for idx, m in enumerate(matches, 1):
        home = m.get("home_team", {})
        away = m.get("away_team", {})
        home_score = m.get("home_score")
        away_score = m.get("away_score")
        status = m.get("status", "upcoming")
        time_str = m.get("host_time") or ""

        score_part = ""
        if home_score is not None and away_score is not None:
            score_part = f" {home_score}{t['score_separator']}{away_score}"

        time_part = f" ({time_str})" if time_str else ""
        status_icon = "🔴" if status == "live" else ("✅" if status == "finished" else "⏳")

        elements.append(
            _markdown(
                f"{idx}. {status_icon} "
                f"**{_team_display(home, lang)}**{score_part} "
                f"**{_team_display(away, lang)}**{time_part}"
            )
        )
        elements.append(_divider())

    # Remove trailing divider
    if elements and elements[-1] == _divider():
        elements.pop()

    return {
        "config": _card_config(),
        "header": _header(t["today_matches"], template="purple"),
        "elements": elements,
    }


def build_ai_analysis_card(
    analysis_text: str,
    *,
    query: str = "",
    lang: str = "zh-CN",
) -> Dict[str, Any]:
    """Build a card wrapping an AI analysis response.

    Truncates *analysis_text* to ~4000 chars to stay within Feishu limits.
    """
    t = _t(lang)

    # Feishu card markdown has a practical length limit
    truncated = analysis_text[:4000] + ("..." if len(analysis_text) > 4000 else "")

    elements: List[Dict[str, Any]] = []
    if query:
        elements.append(_markdown(f"**{t['ai_query']}**: {query}"))
        elements.append(_divider())

    elements.append(_markdown(truncated))

    return {
        "config": _card_config(),
        "header": _header(t["ai_analysis"], template="indigo"),
        "elements": elements,
    }


def build_error_card(
    message: str,
    *,
    lang: str = "zh-CN",
) -> Dict[str, Any]:
    """Build a minimal error card."""
    t = _t(lang)
    return {
        "config": _card_config(),
        "header": _header(t["error_title"], template="red"),
        "elements": [_markdown(message)],
    }
