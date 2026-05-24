"""Bracket (knockout tree) business logic — bridges controllers and MatchRepository."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.match_repo import MatchRepository
from app.schemas.bracket_schema import (
    BracketMatchResponse,
    BracketRoundResponse,
    BracketTeamResponse,
    BracketTreeResponse,
)
from app.utils.timezone import convert_datetime

# Ordered from earliest to latest knockout stage.
_STAGE_ORDER: list[str] = ["R32", "R16", "QF", "SF", "3rd", "F"]

# Human-readable display names (en / zh pairs).
_DISPLAY_NAMES: dict[str, dict[str, str]] = {
    "R32": {"en": "Round of 32", "zh": "三十二强"},
    "R16": {"en": "Round of 16", "zh": "十六强"},
    "QF":  {"en": "Quarter-finals", "zh": "四分之一决赛"},
    "SF":  {"en": "Semi-finals", "zh": "半决赛"},
    "3rd": {"en": "Third-place match", "zh": "三四名决赛"},
    "F":   {"en": "Final", "zh": "决赛"},
}


class BracketService:
    """Orchestrates knockout-bracket business operations.

    Parameters
    ----------
    session:
        An ``AsyncSession`` managed by the caller (dependency injection).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._match_repo = MatchRepository(session)

    # ── public methods ─────────────────────────────────────────────────────

    async def get_full_bracket(
        self,
        *,
        lang: str = "en",
        timezone_name: Optional[str] = None,
    ) -> dict:
        """Return the full knockout bracket tree (R32→R16→QF→SF→3rd→F).

        Each round is grouped by ``stage`` and its matches are sorted by
        ``position`` (ascending).  Teams that are still TBD carry
        ``from_group`` / ``from_position`` context.
        """
        matches = await self._match_repo.get_bracket_matches()

        # Group matches by stage.
        by_stage: dict[str, list] = {s: [] for s in _STAGE_ORDER}
        for m in matches:
            if m.stage in by_stage:
                by_stage[m.stage].append(m)

        rounds: list[dict] = []
        for stage in _STAGE_ORDER:
            stage_matches = sorted(by_stage[stage], key=lambda m: (m.position or 0, m.kickoff_utc))
            match_vos = [_match_to_bracket_vo(m, lang=lang, timezone_name=timezone_name) for m in stage_matches]
            display_name = _DISPLAY_NAMES.get(stage, {}).get(lang, stage)
            rounds.append(BracketRoundResponse(
                round_name=stage,
                display_name=display_name,
                matches=match_vos,
            ).model_dump())

        return BracketTreeResponse(rounds=rounds).model_dump()

    async def get_bracket_by_round(
        self,
        round_name: str,
        *,
        lang: str = "en",
        timezone_name: Optional[str] = None,
    ) -> dict:
        """Return a single round of the bracket.

        Parameters
        ----------
        round_name:
            One of ``R32``, ``R16``, ``QF``, ``SF``, ``3rd``, ``F``.
        """
        normalised = round_name.upper()
        if normalised not in _STAGE_ORDER:
            from app.exceptions.exceptions import NotFoundError
            raise NotFoundError(
                f"Round '{round_name}' is not valid. Expected one of: {', '.join(_STAGE_ORDER)}"
            )

        all_matches = await self._match_repo.get_bracket_matches()
        stage_matches = sorted(
            [m for m in all_matches if m.stage == normalised],
            key=lambda m: (m.position or 0, m.kickoff_utc),
        )

        match_vos = [_match_to_bracket_vo(m, lang=lang, timezone_name=timezone_name) for m in stage_matches]
        display_name = _DISPLAY_NAMES.get(normalised, {}).get(lang, normalised)

        return BracketRoundResponse(
            round_name=normalised,
            display_name=display_name,
            matches=match_vos,
        ).model_dump()

    async def get_predictions(self) -> dict:
        """Return AI-predicted knockout bracket path.

        Currently returns a placeholder.  Phase 3 will integrate with
        the AI service to populate real predictions.
        """
        return {"status": "TBD", "message": "AI bracket predictions will be available in Phase 3."}


# ── module-level helpers ──────────────────────────────────────────────────


def _match_to_bracket_vo(
    match: object,
    *,
    lang: str = "en",
    timezone_name: Optional[str] = None,
) -> dict:
    """Convert a Match ORM object into a BracketMatchResponse dict."""
    home_vo = _build_team_vo(match, "home", lang=lang)
    away_vo = _build_team_vo(match, "away", lang=lang)

    kickoff_str: Optional[str] = None
    if match.kickoff_utc:
        kickoff_str = match.kickoff_utc.isoformat()

    # If a timezone was requested, also compute the local kickoff time.
    if timezone_name and match.kickoff_utc:
        try:
            local_dt = convert_datetime(match.kickoff_utc, timezone_name)
            kickoff_str = local_dt.isoformat()
        except Exception:
            pass

    return BracketMatchResponse(
        id=match.id,
        external_id=match.external_id,
        stage=match.stage,
        home_team=BracketTeamResponse(**home_vo),
        away_team=BracketTeamResponse(**away_vo),
        status=match.status,
        kickoff_utc=kickoff_str,
        position=match.position,
    ).model_dump()


def _build_team_vo(match: object, side: str, *, lang: str = "en") -> dict:
    """Build a BracketTeamResponse dict for the given side (home/away).

    If the team is a real row in ``teams``, return full info.
    If the team code is ``TBD`` (or similar placeholder), extract
    ``from_group`` / ``from_position`` from the match's bracket linkage.
    """
    team_obj = match.home_team if side == "home" else match.away_team
    score = match.home_score if side == "home" else match.away_score

    vo: dict = {
        "id": team_obj.id,
        "name": team_obj.name,
        "name_zh": team_obj.name_zh,
        "code": team_obj.code,
        "flag": team_obj.flag,
        "score": score,
        "from_group": None,
        "from_position": None,
    }

    # Promote Chinese name when requested.
    if lang == "zh" and vo["name_zh"]:
        vo["name"] = vo["name_zh"]

    # If the team code indicates a TBD placeholder, try to infer qualifying
    # context from the match's group_label or external_id naming convention.
    if team_obj.code and team_obj.code.upper().startswith("TBD"):
        vo["id"] = None
        vo["name"] = "TBD"
        vo["name_zh"] = "待定"
        vo["code"] = None
        vo["flag"] = None
        _infer_tbd_context(match, side, vo)

    return vo


def _infer_tbd_context(match: object, side: str, vo: dict) -> None:
    """Attempt to populate ``from_group`` and ``from_position`` for a TBD team.

    The bracket seeding convention encodes qualifying info in
    ``external_id`` (e.g. ``R32_01``) and the ``position`` field determines
    the home/away slot in the next match.  For R32 matches, the qualifying
    position can be derived from the match ordering within the stage.

    NOTE: Once ``scripts/generate_bracket.py`` is implemented (P1-16), the
    bracket matches will store richer qualifying metadata.  Until then we
    return basic context from the match data available.
    """
    # Placeholder: in a fully seeded bracket, we would look up the
    # originating group match or standing.  For now we set generic context.
    stage = match.stage
    if stage == "R32":
        # Round of 32 teams come from group standings (1st/2nd/3rd).
        # Exact mapping depends on the official FIFA draw; leave generic.
        pass
    elif stage in ("R16", "QF", "SF", "3rd", "F"):
        # Later rounds come from previous round winners.
        pass
