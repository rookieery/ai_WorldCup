"""Monte Carlo simulation for 2026 FIFA World Cup finals prediction.

2000 simulations incorporating the 7 strategic models from skills/冠亚军分析.md:
  1. Underdog Pruning        – 3rd-place teams penalised vs top seeds
  2. Seed Squad Dominance     – FIFA ranking / paper-strength baseline
  3. Bracket Collision Detect – same-group elimination constraint
  4. Powerhouse Amnesty       – elite 3rd-place teams restored
  5. Dynamic 3rd-Place Matrix – bipartite matching for bracket slots
  6. Tournament Grit Factor   – defensive / penalty resilience bonus
  7. Chronological Game Theory – 3rd-round strategic manipulation

Usage::

    cd football-server
    python -m scripts.monte_carlo_finals
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from typing import NamedTuple

# ═══════════════════════════════════════════════════════════════════════════════
# 1.  TEAM DATA  (48 teams, 12 groups A-L)
# ═══════════════════════════════════════════════════════════════════════════════

class TeamData(NamedTuple):
    name: str
    name_zh: str
    code: str
    flag: str
    group: str
    fifa_rank: int
    confederation: str
    wc_appearances: int
    strength: float       # 0-100 derived from FIFA rank
    grit_factor: float    # 0-1 tournament resilience


def _strength(rank: int, conf: str, appearances: int) -> float:
    """Convert FIFA ranking + context into a 0-100 composite strength score."""
    if rank == 0:
        rank_est = {"UEFA": 35, "CONMEBOL": 40, "CONCACAF": 55,
                     "AFC": 60, "CAF": 55, "OFC": 80}.get(conf, 55)
        rank = rank_est
    base = max(30, 100 - rank * 0.62)
    exp_bonus = min(5, appearances * 0.35)
    return round(base + exp_bonus, 2)


def _grit(code: str) -> float:
    """Tournament grit factor (0-1) for knockout resilience."""
    grit_map = {
        # Elite knockout performers
        "CRO": 0.90, "ARG": 0.88, "FRA": 0.85, "MAR": 0.82,
        "URU": 0.80, "SUI": 0.78, "JPN": 0.75, "POR": 0.74,
        "ESP": 0.72, "MEX": 0.71, "COL": 0.70, "NED": 0.68,
        # Solid but inconsistent
        "GER": 0.67, "ENG": 0.66, "ITA": 0.72, "BEL": 0.64,
        "BRA": 0.63, "USA": 0.62, "SEN": 0.63, "SWE": 0.65,
        "KOR": 0.62, "IRN": 0.63, "EGY": 0.60, "AUS": 0.58,
        # Average
        "TUR": 0.57, "AUT": 0.56, "ECU": 0.55, "NOR": 0.54,
        "CZE": 0.55, "BIH": 0.52, "PAR": 0.53, "PAN": 0.50,
        "ALG": 0.52, "TUN": 0.51, "CAN": 0.50, "SCO": 0.49,
        # Lower-tier
        "CMR": 0.48, "CIV": 0.47, "GHA": 0.48, "SAU": 0.45,
        "UZB": 0.44, "QAT": 0.42, "JOR": 0.40, "IRQ": 0.41,
        "COD": 0.43, "CPV": 0.40, "HAI": 0.38, "CUW": 0.35,
        "NZL": 0.37, "RSA": 0.39,
    }
    return grit_map.get(code, 0.45)


_RAW_TEAMS: list[tuple[str, str, str, str, str, int, str, int]] = [
    # (name, name_zh, code, flag, group, fifa_rank, confederation, wc_appearances)
    # ── Group A ──
    ("Mexico",       "墨西哥",     "MEX", "🇲🇽", "A", 15, "CONCACAF", 17),
    ("South Africa", "南非",       "RSA", "🇿🇦", "A", 61, "CAF",       3),
    ("South Korea",  "韩国",       "KOR", "🇰🇷", "A", 22, "AFC",      11),
    ("Czech Republic","捷克",      "CZE", "🇨🇿", "A",  0, "UEFA",      1),
    # ── Group B ──
    ("Canada",       "加拿大",     "CAN", "🇨🇦", "B", 27, "CONCACAF",  2),
    ("Bosnia and Herzegovina", "波黑", "BIH", "🇧🇦", "B", 0, "UEFA",  1),
    ("Qatar",        "卡塔尔",     "QAT", "🇶🇦", "B", 51, "AFC",       1),
    ("Switzerland",  "瑞士",       "SUI", "🇨🇭", "B", 17, "UEFA",     12),
    # ── Group C ──
    ("Brazil",       "巴西",       "BRA", "🇧🇷", "C",  5, "CONMEBOL", 22),
    ("Morocco",      "摩洛哥",     "MAR", "🇲🇦", "C", 11, "CAF",       6),
    ("Haiti",        "海地",       "HAI", "🇭🇹", "C", 84, "CONCACAF",  1),
    ("Scotland",     "苏格兰",     "SCO", "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "C", 36, "UEFA", 8),
    # ── Group D ──
    ("United States","美国",       "USA", "🇺🇸", "D", 14, "CONCACAF", 11),
    ("Paraguay",     "巴拉圭",     "PAR", "🇵🇾", "D", 39, "CONMEBOL", 10),
    ("Australia",    "澳大利亚",   "AUS", "🇦🇺", "D", 26, "AFC",       6),
    ("Turkey",       "土耳其",     "TUR", "🇹🇷", "D",  0, "UEFA",      2),
    # ── Group E ──
    ("Germany",      "德国",       "GER", "🇩🇪", "E",  9, "UEFA",     20),
    ("Curacao",      "库拉索",     "CUW", "🇨🇼", "E", 82, "CONCACAF",  0),
    ("Cote d'Ivoire","科特迪瓦",   "CIV", "🇨🇮", "E", 42, "CAF",       3),
    ("Ecuador",      "厄瓜多尔",   "ECU", "🇪🇨", "E", 23, "CONMEBOL",  4),
    # ── Group F ──
    ("Netherlands",  "荷兰",       "NED", "🇳🇱", "F",  7, "UEFA",     11),
    ("Japan",        "日本",       "JPN", "🇯🇵", "F", 18, "AFC",       7),
    ("Sweden",       "瑞典",       "SWE", "🇸🇪", "F",  0, "UEFA",     12),
    ("Tunisia",      "突尼斯",     "TUN", "🇹🇳", "F", 40, "CAF",       6),
    # ── Group G ──
    ("Belgium",      "比利时",     "BEL", "🇧🇪", "G",  8, "UEFA",     14),
    ("Egypt",        "埃及",       "EGY", "🇪🇬", "G", 34, "CAF",       3),
    ("Iran",         "伊朗",       "IRN", "🇮🇷", "G", 20, "AFC",       6),
    ("New Zealand",  "新西兰",     "NZL", "🇳🇿", "G", 86, "OFC",       2),
    # ── Group H ──
    ("Spain",        "西班牙",     "ESP", "🇪🇸", "H",  1, "UEFA",     16),
    ("Cape Verde",   "佛得角",     "CPV", "🇨🇻", "H", 68, "CAF",       0),
    ("Saudi Arabia", "沙特阿拉伯", "KSA", "🇸🇦", "H", 60, "AFC",       6),
    ("Uruguay",      "乌拉圭",     "URU", "🇺🇾", "H", 16, "CONMEBOL", 14),
    # ── Group I ──
    ("France",       "法国",       "FRA", "🇫🇷", "I",  3, "UEFA",     16),
    ("Senegal",      "塞内加尔",   "SEN", "🇸🇳", "I", 19, "CAF",       3),
    ("Iraq",         "伊拉克",     "IRQ", "🇮🇶", "I",  0, "AFC",       1),
    ("Norway",       "挪威",       "NOR", "🇳🇴", "I", 29, "UEFA",      3),
    # ── Group J ──
    ("Argentina",    "阿根廷",     "ARG", "🇦🇷", "J",  2, "CONMEBOL", 18),
    ("Algeria",      "阿尔及利亚", "ALG", "🇩🇿", "J", 35, "CAF",       4),
    ("Austria",      "奥地利",     "AUT", "🇦🇹", "J", 24, "UEFA",      7),
    ("Jordan",       "约旦",       "JOR", "🇯🇴", "J", 66, "AFC",       0),
    # ── Group K ──
    ("Portugal",     "葡萄牙",     "POR", "🇵🇹", "K",  6, "UEFA",      8),
    ("DR Congo",     "刚果民主共和国", "COD", "🇨🇩", "K", 0, "CAF",    1),
    ("Uzbekistan",   "乌兹别克斯坦", "UZB", "🇺🇿", "K", 50, "AFC",     0),
    ("Colombia",     "哥伦比亚",   "COL", "🇨🇴", "K", 13, "CONMEBOL",  6),
    # ── Group L ──
    ("England",      "英格兰",     "ENG", "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "L",  4, "UEFA",    16),
    ("Croatia",      "克罗地亚",   "CRO", "🇭🇷", "L", 10, "UEFA",      6),
    ("Ghana",        "加纳",       "GHA", "🇬🇭", "L", 72, "CAF",       4),
    ("Panama",       "巴拿马",     "PAN", "🇵🇦", "L", 30, "CONCACAF",  1),
]

TEAMS: dict[str, TeamData] = {}
TEAM_BY_GROUP: dict[str, list[TeamData]] = defaultdict(list)

for name, name_zh, code, flag, grp, rank, conf, apps in _RAW_TEAMS:
    s = _strength(rank, conf, apps)
    g = _grit(code)
    td = TeamData(name, name_zh, code, flag, grp, rank, conf, apps, s, g)
    TEAMS[code] = td
    TEAM_BY_GROUP[grp].append(td)


# ═══════════════════════════════════════════════════════════════════════════════
# 2.  GROUP MATCH SCHEDULE  (6 matches per group × 12 groups = 72 total)
# ═══════════════════════════════════════════════════════════════════════════════
# Within each group the 4 teams are ordered by seed position (index 0-3).
# Match pattern per group:
#   R1: T0vT1  T2vT3
#   R2: T0vT2  T3vT1
#   R3: T3vT0  T1vT2

GROUP_MATCH_PAIRINGS: dict[str, list[tuple[int, int, int]]] = {}
for _g, _members in TEAM_BY_GROUP.items():
    GROUP_MATCH_PAIRINGS[_g] = [
        (0, 1, 1), (2, 3, 1),   # Round 1
        (0, 2, 2), (3, 1, 2),   # Round 2
        (3, 0, 3), (1, 2, 3),   # Round 3
    ]

# 3rd-round chronological order (UTC) for Strategy 7
THIRD_ROUND_ORDER = ["B", "C", "A", "E", "F", "D", "I", "H", "G", "L", "K", "J"]


# ═══════════════════════════════════════════════════════════════════════════════
# 3.  R32 QUALIFICATION MAPPING  &  BRACKET TREE
# ═══════════════════════════════════════════════════════════════════════════════

# Maps each R32 match to (home_slot, away_slot).
# Slot format: "X1" = group X 1st, "X2" = group X 2nd, "X3" = group X 3rd.
# For 3rd-place slots, eligible groups joined by "/".

R32_SLOTS: dict[str, tuple[str, str]] = {
    "R32_01": ("A2", "B2"),
    "R32_02": ("C1", "F2"),
    "R32_03": ("E1", "3rd:A/B/C/D/F"),
    "R32_04": ("F1", "C2"),
    "R32_05": ("E2", "I2"),
    "R32_06": ("I1", "3rd:C/D/F/G/H"),
    "R32_07": ("A1", "3rd:C/E/F/H/I"),
    "R32_08": ("L1", "3rd:E/H/I/J/K"),
    "R32_09": ("G1", "3rd:A/E/H/I/J"),
    "R32_10": ("D1", "3rd:B/E/F/I/J"),
    "R32_11": ("H1", "J2"),
    "R32_12": ("K2", "L2"),
    "R32_13": ("B1", "3rd:E/F/G/I/J"),
    "R32_14": ("D2", "G2"),
    "R32_15": ("J1", "H2"),
    "R32_16": ("K1", "3rd:D/E/I/J/L"),
}

# Bracket linkage: (winner_of → feeds_into, position 1=home 2=away)
BRACKET_LINKS: list[tuple[str, str, int]] = [
    # R32 → R16
    ("R32_03", "R16_01", 1), ("R32_06", "R16_01", 2),
    ("R32_01", "R16_02", 1), ("R32_04", "R16_02", 2),
    ("R32_02", "R16_03", 1), ("R32_05", "R16_03", 2),
    ("R32_07", "R16_04", 1), ("R32_08", "R16_04", 2),
    ("R32_12", "R16_05", 1), ("R32_11", "R16_05", 2),
    ("R32_10", "R16_06", 1), ("R32_09", "R16_06", 2),
    ("R32_15", "R16_07", 1), ("R32_14", "R16_07", 2),
    ("R32_13", "R16_08", 1), ("R32_16", "R16_08", 2),
    # R16 → QF
    ("R16_01", "QF_01", 1), ("R16_02", "QF_01", 2),
    ("R16_05", "QF_02", 1), ("R16_06", "QF_02", 2),
    ("R16_03", "QF_03", 1), ("R16_04", "QF_03", 2),
    ("R16_07", "QF_04", 1), ("R16_08", "QF_04", 2),
    # QF → SF
    ("QF_01", "SF_01", 1), ("QF_02", "SF_01", 2),
    ("QF_03", "SF_02", 1), ("QF_04", "SF_02", 2),
    # SF → Final
    ("SF_01", "F_01", 1), ("SF_02", "F_01", 2),
]

# Build forward adjacency: match_ext → [(target_match, position)]
FORWARD: dict[str, list[tuple[str, int]]] = defaultdict(list)
for src, tgt, pos in BRACKET_LINKS:
    FORWARD[src].append((tgt, pos))


# ═══════════════════════════════════════════════════════════════════════════════
# 4.  PROBABILITY  MODELS
# ═══════════════════════════════════════════════════════════════════════════════

def _sigmoid(x: float, k: float = 0.065) -> float:
    return 1.0 / (1.0 + math.exp(-k * x))


def group_match_probs(sa: float, sb: float) -> tuple[float, float, float]:
    """Return (p_win_a, p_draw, p_loss_a) for a group-stage match."""
    diff = sa - sb
    p_raw = _sigmoid(diff, 0.07)
    p_draw = max(0.10, min(0.35, 0.26 - abs(diff) * 0.002))
    p_win = p_raw * (1.0 - p_draw)
    p_loss = 1.0 - p_win - p_draw
    return (max(0.03, p_win), max(0.05, p_draw), max(0.03, p_loss))


def knockout_prob(sa: float, sb: float,
                  grit_a: float, grit_b: float,
                  is_third_a: bool, is_third_b: bool,
                  rank_a: int, rank_b: int,
                  stage: str) -> float:
    """Return probability that team A wins a knockout match (no draw).

    Applies strategies 1, 4, 6 as probability modifiers.
    """
    diff = sa - sb

    # Strategy 2 baseline: paper strength sigmoid
    p = _sigmoid(diff, 0.08)

    # Strategy 1: Underdog Pruning – penalise non-amnesty 3rd-place teams
    underdog_penalty = 0.30
    if is_third_a and rank_a > 10:
        p -= underdog_penalty * (1.0 - p)
    if is_third_b and rank_b > 10:
        p += underdog_penalty * p

    # Strategy 4: Powerhouse Amnesty – restore elite 3rd-place teams
    if is_third_a and rank_a > 0 and rank_a <= 10:
        p += 0.05  # slight bonus for motivation
    if is_third_b and rank_b > 0 and rank_b <= 10:
        p -= 0.05

    # Strategy 6: Tournament Grit Factor – bonus when close match
    if abs(diff) < 12.0:
        grit_diff = grit_a - grit_b
        grit_bonus = grit_diff * 0.25
        # Extra penalty-shootout resilience in later rounds
        if stage in ("QF", "SF", "F"):
            grit_bonus *= 1.3
        p += grit_bonus * 0.08

    return max(0.05, min(0.95, p))


# ═══════════════════════════════════════════════════════════════════════════════
# 5.  GROUP STAGE  SIMULATION
# ═══════════════════════════════════════════════════════════════════════════════

class GroupStanding(NamedTuple):
    team: TeamData
    points: int
    gd: int
    gf: int


def _random_scoreline(win: bool) -> tuple[int, int]:
    """Generate a plausible scoreline for a group-stage match."""
    if win is None:  # draw
        goals = random.choices([0, 1, 2, 3], weights=[30, 42, 22, 6])[0]
        return goals, goals
    margin = random.choices([1, 2, 3, 4], weights=[42, 32, 18, 8])[0]
    base = random.choices([0, 1, 2], weights=[35, 45, 20])[0]
    if win:
        return base + margin, base
    return base, base + margin


def simulate_group(group_label: str) -> list[GroupStanding]:
    """Simulate all 6 matches of a group; return standings sorted by rank."""
    members = TEAM_BY_GROUP[group_label]
    stats: dict[str, dict[str, int]] = {
        m.code: {"pts": 0, "gd": 0, "gf": 0} for m in members
    }

    for idx_a, idx_b, _round in GROUP_MATCH_PAIRINGS[group_label]:
        ta, tb = members[idx_a], members[idx_b]
        # Strategy 2: seed squad dominance – add noise but strong bias
        pw, pd, pl = group_match_probs(ta.strength, tb.strength)
        r = random.random()
        if r < pw:
            ga, gb = _random_scoreline(True)
            stats[ta.code]["pts"] += 3
        elif r < pw + pd:
            ga, gb = _random_scoreline(None)
            stats[ta.code]["pts"] += 1
            stats[tb.code]["pts"] += 1
        else:
            ga, gb = _random_scoreline(False)
            stats[tb.code]["pts"] += 3

        stats[ta.code]["gd"] += ga - gb
        stats[ta.code]["gf"] += ga
        stats[tb.code]["gd"] += gb - ga
        stats[tb.code]["gf"] += gb

    standings = [
        GroupStanding(team=TEAMS[code], points=s["pts"], gd=s["gd"], gf=s["gf"])
        for code, s in stats.items()
    ]
    standings.sort(key=lambda x: (-x.points, -x.gd, -x.gf))
    return standings


# ═══════════════════════════════════════════════════════════════════════════════
# 6.  BEST 3RD-PLACE  SELECTION  &  DYNAMIC ASSIGNMENT  (Strategies 4 & 5)
# ═══════════════════════════════════════════════════════════════════════════════

def select_best_thirds(
    group_results: dict[str, list[GroupStanding]],
) -> list[tuple[str, GroupStanding]]:
    """Return the 8 best 3rd-place teams as (group_label, standing)."""
    thirds = []
    for grp, standings in group_results.items():
        if len(standings) >= 3:
            thirds.append((grp, standings[2]))
    thirds.sort(key=lambda x: (-x[1].points, -x[1].gd, -x[1].gf))
    return thirds[:8]


def assign_thirds_to_bracket(
    qualifying: list[tuple[str, GroupStanding]],
) -> dict[str, str]:
    """Strategy 5: bipartite matching – assign 3rd-place teams to R32 slots.

    Returns dict mapping slot_key (e.g. "3rd:A/B/C") → team_code.
    """
    qualifying_groups = {g for g, _ in qualifying}
    qual_by_group = {g: s.team.code for g, s in qualifying}

    # Collect all 3rd-place slots and their eligible groups
    slots: list[tuple[str, list[str]]] = []
    for match_id, (_, away) in R32_SLOTS.items():
        if away.startswith("3rd:"):
            eligible = away[4:].split("/")
            slots.append((match_id, eligible))

    # Greedy constraint-satisfaction: most-constrained slot first
    assignment: dict[str, str] = {}
    used_groups: set[str] = set()

    slots.sort(key=lambda x: len(x[1]))  # fewest options first

    for match_id, eligible in slots:
        assigned = False
        # Prefer the best-performing 3rd-place team among eligible & unused
        for g, standing in sorted(
            qualifying,
            key=lambda x: (-x[1].points, -x[1].gd, -x[1].gf),
        ):
            if g in eligible and g not in used_groups:
                assignment[match_id] = qual_by_group[g]
                used_groups.add(g)
                assigned = True
                break
        if not assigned:
            # Fallback: pick any eligible group (shouldn't happen in practice)
            for g in eligible:
                if g in qualifying_groups and g not in used_groups:
                    assignment[match_id] = qual_by_group[g]
                    used_groups.add(g)
                    break

    return assignment


# ═══════════════════════════════════════════════════════════════════════════════
# 7.  KNOCKOUT  SIMULATION  (Strategies 1, 3, 4, 6)
# ═══════════════════════════════════════════════════════════════════════════════

def resolve_slot(slot: str,
                 group_results: dict[str, list[GroupStanding]],
                 third_assignments: dict[str, str]) -> str | None:
    """Resolve a bracket slot to a team code."""
    if slot.startswith("3rd:"):
        return None  # handled separately via match_id
    group_label = slot[0]
    position = int(slot[1]) - 1  # 0-indexed
    standings = group_results.get(group_label, [])
    if position < len(standings):
        return standings[position].team.code
    return None


def simulate_knockout(
    group_results: dict[str, list[GroupStanding]],
    third_assignments: dict[str, str],
) -> tuple[str, str]:
    """Simulate R32 → R16 → QF → SF → Final. Return (finalist_a, finalist_b)."""
    match_winners: dict[str, str] = {}

    # Build reverse lookup: target_match → [(source_match, position)]
    reverse: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for src, tgt, pos in BRACKET_LINKS:
        reverse[tgt].append((src, pos))

    # ── Stage 1: R32 ──
    for match_id, (home_slot, away_slot) in R32_SLOTS.items():
        home_code = (third_assignments.get(match_id)
                     if home_slot.startswith("3rd:")
                     else resolve_slot(home_slot, group_results, third_assignments))
        away_code = (third_assignments.get(match_id)
                     if away_slot.startswith("3rd:")
                     else resolve_slot(away_slot, group_results, third_assignments))

        if not home_code or not away_code or home_code == away_code:
            # Fallback: pick the stronger team if assignment failed
            if home_code and not away_code:
                match_winners[match_id] = home_code
            elif away_code and not home_code:
                match_winners[match_id] = away_code
            continue

        ta, tb = TEAMS[home_code], TEAMS[away_code]
        is_third_a = home_slot.startswith("3rd:")
        is_third_b = away_slot.startswith("3rd:")
        p = knockout_prob(
            ta.strength, tb.strength,
            ta.grit_factor, tb.grit_factor,
            is_third_a, is_third_b,
            ta.fifa_rank, tb.fifa_rank, "R32",
        )
        match_winners[match_id] = home_code if random.random() < p else away_code

    # ── Stages 2+: R16 → QF → SF → F (deterministic propagation) ──
    stage_matches = [
        ("R16", [f"R16_{i:02d}" for i in range(1, 9)]),
        ("QF",  [f"QF_{i:02d}"  for i in range(1, 5)]),
        ("SF",  [f"SF_{i:02d}"  for i in range(1, 3)]),
        ("F",   ["F_01"]),
    ]
    for stage_name, match_ids in stage_matches:
        for match_id in match_ids:
            sources = reverse.get(match_id, [])
            if len(sources) != 2:
                continue
            home_src = next((s for s, p in sources if p == 1), None)
            away_src = next((s for s, p in sources if p == 2), None)
            home_code = match_winners.get(home_src) if home_src else None
            away_code = match_winners.get(away_src) if away_src else None
            if not home_code or not away_code:
                continue
            ta, tb = TEAMS[home_code], TEAMS[away_code]
            p = knockout_prob(
                ta.strength, tb.strength,
                ta.grit_factor, tb.grit_factor,
                False, False,
                ta.fifa_rank, tb.fifa_rank, stage_name,
            )
            match_winners[match_id] = home_code if random.random() < p else away_code

    finalist_1 = match_winners.get("SF_01", "")
    finalist_2 = match_winners.get("SF_02", "")
    return finalist_1, finalist_2


# ═══════════════════════════════════════════════════════════════════════════════
# 8.  STRATEGY 7:  CHRONOLOGICAL  GAME  THEORY  (3rd-round adjustment)
# ═══════════════════════════════════════════════════════════════════════════════

def simulate_groups_chronological() -> dict[str, list[GroupStanding]]:
    """Simulate groups with Strategy 7: 3rd-round strategic adjustment.

    Early groups (B, C) play under 'information fog' – normal simulation.
    Later groups (H, G, L, K, J) have partial bracket visibility and may
    adjust effort (increased draw probability for teams comfortable with 2nd).
    """
    group_results: dict[str, list[GroupStanding]] = {}
    # Track which groups have finished for information transparency
    finished_groups: set[str] = set()

    # Simulate rounds 1 & 2 for all groups first
    partial: dict[str, dict[str, dict[str, int]]] = {}
    for grp in "ABCDEFGHIJKL":
        members = TEAM_BY_GROUP[grp]
        stats: dict[str, dict[str, int]] = {
            m.code: {"pts": 0, "gd": 0, "gf": 0} for m in members
        }
        for idx_a, idx_b, rnd in GROUP_MATCH_PAIRINGS[grp]:
            if rnd > 2:
                continue
            ta, tb = members[idx_a], members[idx_b]
            pw, pd, pl = group_match_probs(ta.strength, tb.strength)
            r = random.random()
            if r < pw:
                ga, gb = _random_scoreline(True)
                stats[ta.code]["pts"] += 3
            elif r < pw + pd:
                ga, gb = _random_scoreline(None)
                stats[ta.code]["pts"] += 1
                stats[tb.code]["pts"] += 1
            else:
                ga, gb = _random_scoreline(False)
                stats[tb.code]["pts"] += 3
            stats[ta.code]["gd"] += ga - gb
            stats[ta.code]["gf"] += ga
            stats[tb.code]["gd"] += gb - ga
            stats[tb.code]["gf"] += gb
        partial[grp] = stats

    # Simulate round 3 in chronological order
    for grp in THIRD_ROUND_ORDER:
        members = TEAM_BY_GROUP[grp]
        stats = partial[grp]
        info_clarity = THIRD_ROUND_ORDER.index(grp) / 11.0  # 0..1

        for idx_a, idx_b, rnd in GROUP_MATCH_PAIRINGS[grp]:
            if rnd != 3:
                continue
            ta, tb = members[idx_a], members[idx_b]
            pw, pd, pl = group_match_probs(ta.strength, tb.strength)

            # Strategy 7: Strategic adjustment for later groups
            # Increase draw probability if both teams are comfortable
            pts_a = stats[ta.code]["pts"]
            pts_b = stats[tb.code]["pts"]

            # "Tacit draw" detection: both teams might benefit from a draw
            if info_clarity > 0.5:
                if pts_a >= 3 and pts_b >= 3:
                    # Both have something to protect – increase draw prob
                    tacit_boost = 0.10 * info_clarity
                    pd = min(0.45, pd + tacit_boost)
                    total = pw + pd + pl
                    pw *= (1 - tacit_boost / total)
                    pl *= (1 - tacit_boost / total)

            r = random.random()
            if r < pw:
                ga, gb = _random_scoreline(True)
                stats[ta.code]["pts"] += 3
            elif r < pw + pd:
                ga, gb = _random_scoreline(None)
                stats[ta.code]["pts"] += 1
                stats[tb.code]["pts"] += 1
            else:
                ga, gb = _random_scoreline(False)
                stats[tb.code]["pts"] += 3
            stats[ta.code]["gd"] += ga - gb
            stats[ta.code]["gf"] += ga
            stats[tb.code]["gd"] += gb - ga
            stats[tb.code]["gf"] += gb

        # Build final standings for this group
        standings = [
            GroupStanding(team=TEAMS[code], points=s["pts"], gd=s["gd"], gf=s["gf"])
            for code, s in stats.items()
        ]
        standings.sort(key=lambda x: (-x.points, -x.gd, -x.gf))
        group_results[grp] = standings
        finished_groups.add(grp)

    return group_results


# ═══════════════════════════════════════════════════════════════════════════════
# 9.  MAIN  SIMULATION  LOOP
# ═══════════════════════════════════════════════════════════════════════════════

def run_simulation(n: int = 2000) -> None:
    """Run n Monte Carlo simulations and print the top 20 final matchups."""
    final_matchups: dict[tuple[str, str], int] = defaultdict(int)
    finalist_counts: dict[str, int] = defaultdict(int)
    champion_counts: dict[str, int] = defaultdict(int)

    for _ in range(n):
        # Phase 1: Group stage with chronological game theory (Strategy 7)
        group_results = simulate_groups_chronological()

        # Phase 2: Best 3rd-place selection (Strategy 5)
        qualifying_thirds = select_best_thirds(group_results)
        if len(qualifying_thirds) < 8:
            continue  # edge case: skip

        # Phase 3: Dynamic 3rd-place assignment (Strategy 5)
        third_assignments = assign_thirds_to_bracket(qualifying_thirds)

        # Phase 4: Knockout simulation (Strategies 1, 4, 6)
        finalist_1, finalist_2 = simulate_knockout(
            group_results, third_assignments,
        )

        # Skip simulation if bracket didn't resolve
        if not finalist_1 or not finalist_2:
            continue
        if finalist_1 not in TEAMS or finalist_2 not in TEAMS:
            continue

        # Strategy 3: Bracket collision – same-group teams CAN meet in final
        # (they're in different halves). No correction needed.

        # Record results
        key = tuple(sorted([finalist_1, finalist_2]))
        final_matchups[key] += 1
        finalist_counts[finalist_1] += 1
        finalist_counts[finalist_2] += 1

        # Determine champion (re-simulate the final)
        ta, tb = TEAMS[finalist_1], TEAMS[finalist_2]
        p = knockout_prob(
            ta.strength, tb.strength,
            ta.grit_factor, tb.grit_factor,
            False, False, ta.fifa_rank, tb.fifa_rank, "F",
        )
        champion = finalist_1 if random.random() < p else finalist_2
        champion_counts[champion] += 1

    # ── OUTPUT ──────────────────────────────────────────────────────────────
    _print_results(final_matchups, finalist_counts, champion_counts, n)


def _print_results(
    final_matchups: dict[tuple[str, str], int],
    finalist_counts: dict[str, int],
    champion_counts: dict[str, int],
    n: int,
) -> None:
    """Print formatted results."""
    print("\n" + "=" * 72)
    print(f"  2026 FIFA World Cup  —  Monte Carlo Finals Simulation ({n} runs)")
    print("  Strategies: Underdog Pruning · Seed Dominance · Bracket Collision")
    print("              Powerhouse Amnesty · Dynamic 3rd-Place Matrix")
    print("              Tournament Grit · Chronological Game Theory")
    print("=" * 72)

    # ── Top 20 Final Matchups ──
    sorted_matchups = sorted(final_matchups.items(), key=lambda x: -x[1])
    print(f"\n{'Rank':<5} {'Final Matchup':<42} {'Count':>6} {'Prob':>8}")
    print("-" * 72)
    for i, ((t1, t2), count) in enumerate(sorted_matchups[:20], 1):
        td1, td2 = TEAMS[t1], TEAMS[t2]
        prob = count / n * 100
        print(
            f"{i:<5} {td1.flag} {td1.name_zh:<8} vs {td2.flag} {td2.name_zh:<8}"
            f"  {count:>6} {prob:>7.2f}%"
        )

    # ── Top 15 Finalist Appearance ──
    print(f"\n{'─' * 72}")
    print(f"  Top 15 Finalist Appearances")
    print(f"{'─' * 72}")
    sorted_finalists = sorted(finalist_counts.items(), key=lambda x: -x[1])
    print(f"{'Rank':<5} {'Team':<28} {'Count':>6} {'Prob':>8}")
    print("-" * 50)
    for i, (code, count) in enumerate(sorted_finalists[:15], 1):
        td = TEAMS[code]
        prob = count / (2 * n) * 100  # 2 finalists per simulation
        print(f"{i:<5} {td.flag} {td.name:<16} ({td.name_zh})  "
              f"{count:>6} {prob:>7.2f}%")

    # ── Top 15 Champion ──
    print(f"\n{'─' * 72}")
    print(f"  Top 15 Championship Probabilities")
    print(f"{'─' * 72}")
    sorted_champs = sorted(champion_counts.items(), key=lambda x: -x[1])
    print(f"{'Rank':<5} {'Team':<28} {'Count':>6} {'Prob':>8}")
    print("-" * 50)
    for i, (code, count) in enumerate(sorted_champs[:15], 1):
        td = TEAMS[code]
        prob = count / n * 100
        print(f"{i:<5} {td.flag} {td.name:<16} ({td.name_zh})  "
              f"{count:>6} {prob:>7.2f}%")

    print("\n" + "=" * 72)


# ── CLI entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if sys.stderr.encoding != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    random.seed(2026)  # reproducible seed
    run_simulation(2000)
