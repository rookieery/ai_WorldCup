"""Initial schema — teams, venues, matches, group_standings, match_events

Revision ID: 001
Revises:
Create Date: 2026-05-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── teams ──────────────────────────────────────────────────────────
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("name_zh", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=3), nullable=False),
        sa.Column("flag", sa.String(length=20), nullable=False),
        sa.Column("fifa_ranking", sa.Integer(), nullable=False),
        sa.Column("group_label", sa.String(length=1), nullable=False),
        sa.Column("confederation", sa.String(length=20), nullable=False),
        sa.Column("world_cup_appearances", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.UniqueConstraint("name"),
    )

    # ── venues ─────────────────────────────────────────────────────────
    op.create_table(
        "venues",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("country", sa.String(length=100), nullable=False),
        sa.Column("timezone", sa.String(length=50), nullable=False),
        sa.Column("utc_offset", sa.String(length=10), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── group_standings ────────────────────────────────────────────────
    op.create_table(
        "group_standings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("group_label", sa.String(length=1), nullable=False),
        sa.Column("played", sa.Integer(), nullable=False),
        sa.Column("won", sa.Integer(), nullable=False),
        sa.Column("drawn", sa.Integer(), nullable=False),
        sa.Column("lost", sa.Integer(), nullable=False),
        sa.Column("goals_for", sa.Integer(), nullable=False),
        sa.Column("goals_against", sa.Integer(), nullable=False),
        sa.Column("goal_difference", sa.Integer(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id"),
    )

    # ── matches ────────────────────────────────────────────────────────
    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("external_id", sa.String(length=50), nullable=False),
        sa.Column("home_team_id", sa.Integer(), nullable=False),
        sa.Column("away_team_id", sa.Integer(), nullable=False),
        sa.Column("venue_id", sa.Integer(), nullable=False),
        sa.Column("stage", sa.String(length=20), nullable=False),
        sa.Column("group_label", sa.String(length=1), nullable=True),
        sa.Column("round", sa.String(length=30), nullable=False),
        sa.Column("match_day", sa.Integer(), nullable=True),
        sa.Column("kickoff_utc", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("home_score", sa.Integer(), nullable=True),
        sa.Column("away_score", sa.Integer(), nullable=True),
        sa.Column("is_big_match", sa.Boolean(), nullable=False),
        sa.Column("activity_level", sa.Integer(), nullable=False),
        sa.Column("next_match_id", sa.Integer(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["away_team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["home_team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["next_match_id"], ["matches.id"]),
        sa.ForeignKeyConstraint(["venue_id"], ["venues.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_id"),
    )

    # ── match_events ───────────────────────────────────────────────────
    op.create_table(
        "match_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("match_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=30), nullable=False),
        sa.Column("minute", sa.Integer(), nullable=False),
        sa.Column("team_side", sa.String(length=10), nullable=False),
        sa.Column("player_name", sa.String(length=150), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("match_events")
    op.drop_table("matches")
    op.drop_table("group_standings")
    op.drop_table("venues")
    op.drop_table("teams")
