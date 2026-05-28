"""Markdown schedule parser for the 2026 FIFA World Cup group-stage data file.

Reads ``data/2026_FIFA_World_Cup_Group_Stage.md`` and returns a list of
structured :class:`ParsedMatch` objects covering all **72 group-stage fixtures**.

Usage::

    from app.utils.markdown_parser import MarkdownParser

    parser = MarkdownParser()
    matches = parser.parse()  # list[ParsedMatch]
    assert len(matches) == 72
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

_DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data"
_DEFAULT_FILENAME = "2026_FIFA_World_Cup_Group_Stage.md"

# Regex patterns ---------------------------------------------------------------

# Matches group headers like "### A组" or "### L组"
_RE_GROUP_HEADER = re.compile(r"^###\s+([A-L])组\s*$")

# Matches table data rows: "| 第1轮 | 6月11日 | 墨西哥 vs 南非 | ..."
_RE_TABLE_ROW = re.compile(r"^\|\s*(第\d+轮)\s*\|\s*(\S+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|")

# Chinese month/day pattern inside a date cell like "6月11日"
_RE_CHINESE_DATE = re.compile(r"(\d+)月(\d+)日")

# Round number extraction from "第1轮"
_RE_ROUND_NUM = re.compile(r"第(\d+)轮")


# ── Data model ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ParsedMatch:
    """A single parsed group-stage fixture extracted from the markdown source.

    Attributes
    ----------
    group_label:
        Group letter ``A``–``L``.
    round_num:
        Round number within the group (1, 2, or 3).
    match_date:
        Fixture date (year forced to **2026**, time is midnight UTC).
    home_team_zh:
        Home team name in Chinese (as written in the markdown).
    away_team_zh:
        Away team name in Chinese.
    fifa_ranking_home:
        Pre-tournament FIFA ranking of the home team, or ``None`` when the
        ranking was unknown at the time of writing (marked ``-``).
    fifa_ranking_away:
        Same, for the away team.
    """

    group_label: str
    round_num: int
    match_date: date
    home_team_zh: str
    away_team_zh: str
    fifa_ranking_home: Optional[int] = None
    fifa_ranking_away: Optional[int] = None


# ── Parser ────────────────────────────────────────────────────────────────────


class MarkdownParser:
    """Stateless parser that reads the group-stage markdown and returns
    structured match data.

    Parameters
    ----------
    file_path:
        Absolute or relative path to the markdown file.  When omitted, the
        parser looks for ``data/2026_FIFA_World_Cup_Group_Stage.md`` relative
        to the repository root.
    year:
        Tournament year (default **2026**).
    """

    def __init__(
        self,
        file_path: Optional[str | Path] = None,
        year: int = 2026,
    ) -> None:
        if file_path is not None:
            self._path = Path(file_path)
        else:
            self._path = _DEFAULT_DATA_DIR / _DEFAULT_FILENAME
        self._year = year

    # ── Public API ─────────────────────────────────────────────────────────

    def parse(self) -> list[ParsedMatch]:
        """Parse the markdown file and return all group-stage matches.

        Returns
        -------
        list[ParsedMatch]
            Exactly **72** matches (12 groups × 6 matches each) when parsing
            the standard source file.

        Raises
        ------
        FileNotFoundError
            If the markdown data file cannot be located.
        ValueError
            If the file content is malformed or the expected number of matches
            cannot be found.
        """
        text = self._read_file()
        matches = self._extract_matches(text)
        logger.info("Parsed %d group-stage matches from %s", len(matches), self._path)
        return matches

    # ── Internal helpers ───────────────────────────────────────────────────

    def _read_file(self) -> str:
        """Read and return the markdown file contents with UTF-8 encoding."""
        if not self._path.exists():
            raise FileNotFoundError(f"Data file not found: {self._path}")
        return self._path.read_text(encoding="utf-8")

    def _extract_matches(self, text: str) -> list[ParsedMatch]:
        """Walk through the markdown lines and extract match records."""
        matches: list[ParsedMatch] = []
        current_group: Optional[str] = None

        for line in text.splitlines():
            # 1. Check for a group header
            group_match = _RE_GROUP_HEADER.match(line.strip())
            if group_match:
                current_group = group_match.group(1)
                continue

            # 2. Try to parse a table data row (skip header / separator rows)
            if current_group is None:
                continue

            row_match = _RE_TABLE_ROW.match(line.strip())
            if not row_match:
                continue

            round_str = row_match.group(1)   # e.g. "第1轮"
            date_str = row_match.group(2)     # e.g. "6月11日"
            matchup_str = row_match.group(3)  # e.g. "墨西哥 vs 南非"
            ranking_str = row_match.group(4)  # e.g. "15 / 61" or "- / 61"

            parsed_round = self._parse_round(round_str)
            parsed_date = self._parse_date(date_str)
            home_zh, away_zh = self._parse_matchup(matchup_str)
            rank_home, rank_away = self._parse_rankings(ranking_str)

            matches.append(
                ParsedMatch(
                    group_label=current_group,
                    round_num=parsed_round,
                    match_date=parsed_date,
                    home_team_zh=home_zh,
                    away_team_zh=away_zh,
                    fifa_ranking_home=rank_home,
                    fifa_ranking_away=rank_away,
                )
            )

        return matches

    # ── Field-level parsers ────────────────────────────────────────────────

    def _parse_round(self, round_str: str) -> int:
        """Extract the numeric round from a string like ``'第1轮'``."""
        m = _RE_ROUND_NUM.search(round_str)
        if not m:
            raise ValueError(f"Cannot parse round number from: {round_str!r}")
        return int(m.group(1))

    def _parse_date(self, date_str: str) -> date:
        """Convert a Chinese date like ``'6月11日'`` to a :class:`date`.

        The year is set to the tournament year (default 2026).
        """
        m = _RE_CHINESE_DATE.search(date_str)
        if not m:
            raise ValueError(f"Cannot parse date from: {date_str!r}")
        month = int(m.group(1))
        day = int(m.group(2))
        return date(self._year, month, day)

    @staticmethod
    def _parse_matchup(matchup_str: str) -> tuple[str, str]:
        """Split ``'墨西哥 vs 南非'`` into ``(home, away)`` Chinese names.

        Handles edge cases where team names themselves contain spaces by
        splitting only on the first `` vs `` occurrence.
        """
        parts = matchup_str.split(" vs ", maxsplit=1)
        if len(parts) != 2:
            raise ValueError(f"Cannot parse matchup: {matchup_str!r}")
        home = parts[0].strip()
        away = parts[1].strip()
        return home, away

    @staticmethod
    def _parse_rankings(ranking_str: str) -> tuple[Optional[int], Optional[int]]:
        """Parse ``'15 / 61'`` or ``'- / 61'`` into ``(home_rank, away_rank)``.

        Returns ``None`` for any component that is ``-``.
        """
        parts = ranking_str.split("/")
        if len(parts) != 2:
            return None, None

        def _to_int(val: str) -> Optional[int]:
            val = val.strip()
            if val == "-" or not val:
                return None
            try:
                return int(val)
            except ValueError:
                return None

        return _to_int(parts[0]), _to_int(parts[1])
